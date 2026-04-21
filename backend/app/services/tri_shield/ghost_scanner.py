"""
Module C — Ghost Scanner
------------------------
Detects "Ghost Children": fictitious child enrollments used to claim
government subsidies (PDS rations, child welfare schemes).

Key signal: `age_0_5` column from the enrollment CSV represents
children aged 0–5 enrolled at a pincode. A healthy ghost_child_ratio
(age_0_5 / total_enrollments) sits at ~5–10% in most districts.

Suspicious pattern:
  - ghost_child_ratio spikes above the district's own 90th-percentile
  - OR raw age_0_5 count is anomalously high for that pincode

Input : merged DataFrame (preprocessor output)
Output: df with `ghost_scanner_flag` (bool) and `ghost_child_zscore` (float)
"""

import pandas as pd
import numpy as np
import logging

from app.core.config import settings
from app.core.geography import is_low_population_territory

logger = logging.getLogger(__name__)

# If ghost_child_ratio exceeds this absolute value, always flag.
# Raised from 0.40 to 0.55 — 55% of daily enrollments being 0–5 yr-olds
# is a far stronger signal and sharply cuts false positives on days
# with naturally skewed age distributions (e.g. post-Anganwadi drives).
HARD_RATIO_THRESHOLD = 0.55

# Z-score threshold within district's own distribution. Tightened from
# 2.5σ to 3.0σ so we only flag genuinely extreme within-district spikes.
ZSCORE_THRESHOLD = 3.0


def run(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Per-district z-score of ghost_child_ratio
    def district_zscore(group: pd.Series) -> pd.Series:
        mean = group.mean()
        std  = group.std()
        # Require at least a small amount of variation in the district's
        # history before computing a z-score, otherwise a single outlier
        # against a near-constant backdrop produces meaningless "10^9"
        # values in the generated report.
        if std < 1e-3:
            return pd.Series(np.zeros(len(group)), index=group.index)
        return ((group - mean) / std).clip(lower=-20, upper=20)

    df["ghost_child_zscore"] = (
        df.groupby(["state", "district"])["ghost_child_ratio"]
        .transform(district_zscore)
        .fillna(0)
        .round(3)
    )

    # Volume gate — a pincode must have genuine throughput before any
    # rule is allowed to fire. Prevents tiny-island pincodes where one
    # or two extra infants mathematically break all ratios.
    volume_gate = df["total_enrollments"] >= settings.MIN_TOTAL_ENROLLMENTS_TO_FLAG

    # Suppress flags in ultra-low-population UTs entirely; they generate
    # the classic "Andaman & Nicobar flood" of spurious alerts.
    geo_gate = ~df["state"].astype(str).map(is_low_population_territory)

    hard_flag   = df["ghost_child_ratio"] > HARD_RATIO_THRESHOLD
    zscore_flag = df["ghost_child_zscore"] > ZSCORE_THRESHOLD

    df["ghost_scanner_flag"] = (hard_flag | zscore_flag) & volume_gate & geo_gate

    flagged = df["ghost_scanner_flag"].sum()
    logger.info(
        f"[Ghost Scanner] Flagged {flagged} rows "
        f"(hard={hard_flag.sum()} z={zscore_flag.sum()} "
        f"suppressed_by_volume={int((~volume_gate).sum())} "
        f"suppressed_by_geo={int((~geo_gate).sum())})"
    )
    return df
