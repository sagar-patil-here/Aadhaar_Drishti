"""
Module A — Migration Radar
--------------------------
Detects abnormal enrollment spikes in border districts or any district
that shows a statistically significant deviation from its own historical
enrollment pattern.

Input : merged DataFrame (output of preprocessor)
Output: df with added column `migration_radar_flag` (bool)
        and `migration_zscore` (float)
"""

import pandas as pd
import numpy as np
import logging
from app.core.config import settings
from app.core.geography import is_low_population_territory

logger = logging.getLogger(__name__)


def run(df: pd.DataFrame) -> pd.DataFrame:
    """
    Algorithm:
    1. For each (state, district), compute rolling 30-day mean and std
       of total_enrollments.
    2. Z-score = (today - rolling_mean) / (rolling_std + 1)
    3. Flag rows where |z-score| > MIGRATION_ZSCORE_THRESHOLD
    """
    df = df.sort_values(["state", "district", "date"]).copy()

    def zscore_series(group: pd.Series) -> pd.Series:
        roll = group.rolling(window=30, min_periods=5)
        mean = roll.mean().shift(1)          # shift 1: don't include current day
        std  = roll.std().shift(1).fillna(1)
        # Enforce a meaningful lower bound on std so that a near-constant
        # rolling window doesn't blow the z-score up to 10^9 and make the
        # report unreadable. One enrollment of noise is the floor.
        std = std.clip(lower=1.0)
        z = (group - mean) / std
        # Clip to ±20 so the narrative reads naturally ("5.3 std devs above").
        return z.clip(lower=-20, upper=20)

    df["migration_zscore"] = (
        df.groupby(["state", "district"])["total_enrollments"]
        .transform(zscore_series)
        .fillna(0)
        .round(3)
    )

    # Volume + geography gates — tiny-island pincodes produce huge
    # relative z-scores off tiny absolute counts. Require real traffic.
    volume_gate = df["total_enrollments"] >= settings.MIN_TOTAL_ENROLLMENTS_TO_FLAG
    geo_gate    = ~df["state"].astype(str).map(is_low_population_territory)

    df["migration_radar_flag"] = (
        (df["migration_zscore"].abs() > settings.MIGRATION_ZSCORE_THRESHOLD)
        & volume_gate
        & geo_gate
    )

    flagged = df["migration_radar_flag"].sum()
    logger.info(
        f"[Migration Radar] Flagged {flagged} rows "
        f"(|z|>{settings.MIGRATION_ZSCORE_THRESHOLD}, "
        f"volume>={settings.MIN_TOTAL_ENROLLMENTS_TO_FLAG}, "
        f"low-pop UTs suppressed)"
    )
    return df
