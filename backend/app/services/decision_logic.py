"""
decision_logic.py
-----------------
After anomaly scoring and Tri-Shield module checks, this module:
  1. Assigns severity (HIGH / MEDIUM / LOW) based on score + modules triggered
  2. Splits the DataFrame into secure records and red-flag records
  3. Returns structured dicts ready for DB insertion
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

from app.core.config import settings
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
    df["is_flagged"]    = flags

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

            red_flags.append({
                **base,
                "modules_triggered": ",".join(modules) if modules else "isolation_forest_only",
                "severity":          _severity(float(row["anomaly_score"]), modules),
                "migration_zscore":  float(row.get("migration_zscore", 0)),
                "ghost_child_zscore": float(row.get("ghost_child_zscore", 0)),
            })
        else:
            secure_records.append(base)

    logger.info(
        f"Decision routing: {len(secure_records)} secure, "
        f"{len(red_flags)} flagged "
        f"({100*len(red_flags)/max(len(df),1):.2f}%)"
    )
    return {
        "secure_records": secure_records,
        "red_flags":      red_flags,
        "flagged_count":  len(red_flags),
        "secure_count":   len(secure_records),
    }
