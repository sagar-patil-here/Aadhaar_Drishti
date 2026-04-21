"""
decision_logic.py
-----------------
After anomaly scoring and Tri-Shield module checks, this module:
  1. Assigns severity (HIGH / MEDIUM / LOW) based on score + modules triggered
  2. Builds a human-readable explanation for EVERY flagged row — including
     the ones that only the Isolation Forest caught (no rule fired).
  3. Splits the DataFrame into secure records and red-flag records
  4. Returns structured dicts ready for DB insertion
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple

from app.core.config import settings
from app.core.geography import (
    is_border_state,
    is_low_population_territory,
    priority_score,
)
from app.services.tri_shield import migration_radar, laundering_detector, ghost_scanner

logger = logging.getLogger(__name__)


def _severity(score: float, modules: list[str]) -> str:
    """
    Severity matrix:
      HIGH   — score very negative OR 2+ modules triggered
      MEDIUM — score below threshold OR 1 module triggered
      LOW    — just barely over threshold
    """
    n_modules = len(modules)
    if score < settings.ANOMALY_THRESHOLD * 3 or n_modules >= 2:
        return "HIGH"
    if score < settings.ANOMALY_THRESHOLD * 1.5 or n_modules == 1:
        return "MEDIUM"
    return "LOW"


def run_tri_shield(df: pd.DataFrame) -> pd.DataFrame:
    """Run all three modules and add flag columns."""
    df = migration_radar.run(df)
    df = laundering_detector.run(df)
    df = ghost_scanner.run(df)
    return df


# ─────────────────────────────────────────────
# Reason builder
# ─────────────────────────────────────────────

def _pick_primary_module(modules: List[str]) -> str:
    """
    If multiple rule modules fire on the same row, pick the most
    serious one as the 'primary' bucket. Order of severity:
    ghost > laundering > migration.
    """
    priority = ["ghost_scanner", "laundering_detector", "migration_radar"]
    for p in priority:
        if p in modules:
            return p
    return "isolation_forest_only"


def _dominant_feature(row: pd.Series, feature_stats: Dict[str, Tuple[float, float]]) -> Tuple[str, float]:
    """
    For Isolation-Forest-only flags, find which feature deviates the
    most from the batch mean (in z-score terms). Gives the analyst a
    concrete "this is what looks weird" pointer instead of a black-box
    verdict.
    """
    candidates = [
        "ghost_child_ratio", "bio_demo_ratio_5_17", "bio_demo_ratio_17_",
        "enrollment_velocity", "total_enrollments",
        "age_0_5", "age_5_17", "age_18_greater",
    ]
    best_feat, best_z = "", 0.0
    for f in candidates:
        if f not in feature_stats:
            continue
        mean, std = feature_stats[f]
        if std < 1e-6:
            continue
        z = abs((float(row.get(f, 0)) - mean) / std)
        if z > best_z:
            best_z = z
            best_feat = f
    return best_feat, best_z


_FEATURE_LABELS = {
    "ghost_child_ratio":   "share of 0–5 yr-old enrollments",
    "bio_demo_ratio_5_17": "biometric-to-demographic ratio for minors",
    "bio_demo_ratio_17_":  "biometric-to-demographic ratio for adults",
    "enrollment_velocity": "30-day rolling enrollment volume",
    "total_enrollments":   "daily total enrollments at this pincode",
    "age_0_5":             "raw count of 0–5 yr-old enrollments",
    "age_5_17":            "raw count of 5–17 yr-old enrollments",
    "age_18_greater":      "raw count of 18+ yr-old enrollments",
}


def _build_reason(row: pd.Series, modules: List[str],
                  feature_stats: Dict[str, Tuple[float, float]]) -> str:
    """
    Produces a sentence like:
       "Ghost Scanner triggered: 43% of enrollments are 0–5 yr-olds
        (district norm ~5–10%)."
    If no rule fired, explains the dominant statistical deviation
    picked up by the Isolation Forest.
    """
    parts: list[str] = []

    if "ghost_scanner" in modules:
        r = float(row.get("ghost_child_ratio", 0))
        parts.append(
            f"Ghost Scanner: ghost-child ratio is {r*100:.1f}% of total "
            f"enrollments (healthy districts sit at 5–10%)."
        )
    if "laundering_detector" in modules:
        adult = float(row.get("bio_demo_ratio_17_",  0))
        minor = float(row.get("bio_demo_ratio_5_17", 0))
        worst = max(adult, minor)
        who   = "adult" if adult >= minor else "minor"
        parts.append(
            f"Laundering Detector: {who} biometric updates are {worst:.1f}× "
            f"demographic updates (normal ratio is ~1×), indicating biometric "
            f"cycling on a static demographic shell."
        )
    if "migration_radar" in modules:
        z = float(row.get("migration_zscore", 0))
        parts.append(
            f"Migration Radar: daily enrollments are {abs(z):.1f} standard "
            f"deviations above this district's 30-day rolling average — "
            f"a hallmark of coordinated enrollment surges."
        )

    if not parts:
        # Pure ML catch: no single rule crossed its threshold, but the
        # Isolation Forest saw the combined feature vector as anomalous.
        feat, z = _dominant_feature(row, feature_stats)
        if feat:
            label = _FEATURE_LABELS.get(feat, feat)
            parts.append(
                f"Isolation Forest flagged this row because the {label} "
                f"({float(row.get(feat, 0)):.2f}) deviates {z:.1f}σ from the "
                f"batch mean. No single Tri-Shield rule breached its hard "
                f"threshold, but the combination of features is statistically "
                f"unusual."
            )
        else:
            parts.append(
                "Isolation Forest classified the multi-feature signature of "
                "this record as an outlier relative to the training corpus."
            )

    return " ".join(parts)


def route(
    df: pd.DataFrame,
    scores: np.ndarray,
    flags: np.ndarray,
) -> Dict[str, Any]:
    """
    Parameters
    ----------
    df     : preprocessed DataFrame (after tri_shield enrichment)
    scores : anomaly scores from Isolation Forest, shape (n,)
    flags  : boolean mask, True = flagged

    Returns
    -------
    dict with keys:
      secure_records : list[dict]  — safe rows for DB
      red_flags      : list[dict]  — flagged rows for investigation
      flagged_count  : int
      secure_count   : int
    """
    df = df.copy()
    df["anomaly_score"] = scores.round(5)

    # Apply the same volume + geography gates to Isolation-Forest flags
    # that the rule modules already apply, otherwise "IF-only" flags
    # from Andaman pincodes with 2–3 enrollments would keep showing up.
    volume_gate = df["total_enrollments"] >= settings.MIN_TOTAL_ENROLLMENTS_TO_FLAG
    geo_gate    = ~df["state"].astype(str).map(is_low_population_territory)
    df["is_flagged"] = flags & volume_gate.values & geo_gate.values

    # Pre-compute per-feature (mean, std) on the FULL batch so that the
    # per-row explanation for Isolation-Forest-only flags is deterministic
    # and consistent within a single request.
    feature_stats: Dict[str, Tuple[float, float]] = {}
    for col in [
        "ghost_child_ratio", "bio_demo_ratio_5_17", "bio_demo_ratio_17_",
        "enrollment_velocity", "total_enrollments",
        "age_0_5", "age_5_17", "age_18_greater",
    ]:
        if col in df.columns:
            feature_stats[col] = (float(df[col].mean()), float(df[col].std()))

    secure_records = []
    red_flags      = []

    for _, row in df.iterrows():
        base = {
            "date":     str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"]),
            "state":    row["state"],
            "district": row["district"],
            "pincode":  int(row["pincode"]),
            "age_0_5":             int(row["age_0_5"]),
            "age_5_17":            int(row["age_5_17"]),
            "age_18_greater":      int(row["age_18_greater"]),
            "bio_age_5_17":        int(row["bio_age_5_17"]),
            "bio_age_17_":         int(row["bio_age_17_"]),
            "demo_age_5_17":       int(row["demo_age_5_17"]),
            "demo_age_17_":        int(row["demo_age_17_"]),
            "total_enrollments":   int(row["total_enrollments"]),
            "ghost_child_ratio":   float(row["ghost_child_ratio"]),
            "bio_demo_ratio_5_17": float(row["bio_demo_ratio_5_17"]),
            "bio_demo_ratio_17_":  float(row["bio_demo_ratio_17_"]),
            "enrollment_velocity": float(row["enrollment_velocity"]),
            "anomaly_score":       float(row["anomaly_score"]),
            "is_flagged":          bool(row["is_flagged"]),
        }

        if row["is_flagged"]:
            modules = []
            if row.get("migration_radar_flag"):   modules.append("migration_radar")
            if row.get("laundering_flag"):        modules.append("laundering_detector")
            if row.get("ghost_scanner_flag"):     modules.append("ghost_scanner")

            reason         = _build_reason(row, modules, feature_stats)
            primary_module = _pick_primary_module(modules)

            red_flags.append({
                **base,
                "modules_triggered":  ",".join(modules) if modules else "isolation_forest_only",
                "primary_module":     primary_module,
                "severity":           _severity(float(row["anomaly_score"]), modules),
                "migration_zscore":   float(row.get("migration_zscore", 0)),
                "ghost_child_zscore": float(row.get("ghost_child_zscore", 0)),
                "detection_reason":   reason,
            })
        else:
            secure_records.append(base)

    # Sort so the highest-priority flags sit at the top of the list.
    # The frontend's "Top Flag Report" picks red_flags[0], so this is
    # what makes the downloaded PDF land on a genuinely sensitive
    # record (border state, HIGH severity, real volume) instead of a
    # low-population-UT record that just happened to be first in the
    # DataFrame.
    red_flags.sort(
        key=lambda f: priority_score(
            state=f.get("state"),
            severity=f.get("severity", "LOW"),
            anomaly_score=f.get("anomaly_score", 0.0),
            total_enrollments=f.get("total_enrollments", 0),
        ),
        reverse=True,
    )

    border_count = sum(1 for f in red_flags if is_border_state(f.get("state")))
    logger.info(
        f"Decision routing: {len(secure_records)} secure, "
        f"{len(red_flags)} flagged "
        f"({100*len(red_flags)/max(len(df),1):.2f}%) — "
        f"{border_count} in border states (prioritised)"
    )
    return {
        "secure_records": secure_records,
        "red_flags":      red_flags,
        "flagged_count":  len(red_flags),
        "secure_count":   len(secure_records),
    }
