"""
Module B — Laundering Detector
-------------------------------
Detects identity laundering: disproportionately high biometric update
activity relative to demographic updates.

Legitimate pattern : both bio and demo updates scale together.
Suspicious pattern : bio updates surge while demo stays flat — someone
                     is cycling biometrics on the same demographic shell
                     (classic identity-laundering signature).

Input : merged DataFrame
Output: df with `laundering_flag` (bool) and `bio_demo_ratio_flag` (bool)
"""

import pandas as pd
import logging
from app.core.config import settings
from app.core.geography import is_low_population_territory

logger = logging.getLogger(__name__)

RATIO_THRESHOLD = settings.LAUNDERING_BIO_DEMO_RATIO_THRESHOLD

# Minimum absolute biometric volume required before a ratio is
# considered meaningful. 3 bio updates with 0 demo updates produces
# a huge ratio mathematically, but in practice is just noise.
MIN_BIO_VOLUME = 10


def run(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where bio_demo_ratio_17_ OR bio_demo_ratio_5_17 exceeds
    the configured threshold.

    bio_demo_ratio_17_  = bio_age_17_ / (demo_age_17_ + 1)
    bio_demo_ratio_5_17 = bio_age_5_17 / (demo_age_5_17 + 1)

    These columns are pre-computed in the preprocessor.
    """
    df = df.copy()

    adult_flag = (df["bio_demo_ratio_17_"]  > RATIO_THRESHOLD) & (df["bio_age_17_"]  >= MIN_BIO_VOLUME)
    minor_flag = (df["bio_demo_ratio_5_17"] > RATIO_THRESHOLD) & (df["bio_age_5_17"] >= MIN_BIO_VOLUME)

    # Volume gate: the location needs enough throughput for a ratio to
    # be meaningful. Skips low-traffic pincodes where 5 biometric
    # updates against zero demographic updates produces a huge but
    # operationally meaningless ratio.
    volume_gate = df["total_enrollments"] >= settings.MIN_TOTAL_ENROLLMENTS_TO_FLAG

    # Suppress low-population UTs to avoid the Andaman-style flood.
    geo_gate = ~df["state"].astype(str).map(is_low_population_territory)

    df["laundering_flag"]       = (adult_flag | minor_flag) & volume_gate & geo_gate
    df["laundering_minor_flag"] = minor_flag & volume_gate & geo_gate

    flagged = df["laundering_flag"].sum()
    logger.info(
        f"[Laundering Detector] Flagged {flagged} rows "
        f"(ratio>{RATIO_THRESHOLD}x, bio_volume>={MIN_BIO_VOLUME}). "
        f"Minor-specific: {int(df['laundering_minor_flag'].sum())} "
        f"(suppressed_volume={int((~volume_gate).sum())} "
        f"suppressed_geo={int((~geo_gate).sum())})"
    )
    return df
