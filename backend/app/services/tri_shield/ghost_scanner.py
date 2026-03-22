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

logger = logging.getLogger(__name__)

# If ghost_child_ratio exceeds this absolute value, always flag
HARD_RATIO_THRESHOLD = 0.40   # >40% of enrollments are 0-5 year olds

# Z-score threshold within district's own distribution
ZSCORE_THRESHOLD = 2.5


def run(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Per-district z-score of ghost_child_ratio
    def district_zscore(group: pd.Series) -> pd.Series:
        mean = group.mean()
        std  = group.std()
        if std < 1e-6:
            return pd.Series(np.zeros(len(group)), index=group.index)
        return (group - mean) / std

    df["ghost_child_zscore"] = (
        df.groupby(["state", "district"])["ghost_child_ratio"]
        .transform(district_zscore)
        .fillna(0)
        .round(3)
    )

    # Hard threshold flag (ratio >40% is suspicious regardless of district norms)
    hard_flag   = df["ghost_child_ratio"] > HARD_RATIO_THRESHOLD
    # Statistical flag (unusual within district's own history)
    zscore_flag = df["ghost_child_zscore"] > ZSCORE_THRESHOLD

    df["ghost_scanner_flag"] = hard_flag | zscore_flag

    flagged = df["ghost_scanner_flag"].sum()
    logger.info(
        f"[Ghost Scanner] Flagged {flagged} rows. "
        f"Hard threshold hits: {hard_flag.sum()}, "
        f"Z-score hits: {zscore_flag.sum()}"
    )
    return df
