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

logger = logging.getLogger(__name__)

RATIO_THRESHOLD = settings.LAUNDERING_BIO_DEMO_RATIO_THRESHOLD


def run(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where bio_demo_ratio_17_ OR bio_demo_ratio_5_17 exceeds
    the configured threshold.

    bio_demo_ratio_17_  = bio_age_17_ / (demo_age_17_ + 1)
    bio_demo_ratio_5_17 = bio_age_5_17 / (demo_age_5_17 + 1)

    These columns are pre-computed in the preprocessor.
    """
    df = df.copy()

    # Adult laundering
    adult_flag  = df["bio_demo_ratio_17_"]  > RATIO_THRESHOLD
    # Minor laundering (especially serious — possible child trafficking link)
    minor_flag  = df["bio_demo_ratio_5_17"] > RATIO_THRESHOLD

    df["laundering_flag"]       = adult_flag | minor_flag
    df["laundering_minor_flag"] = minor_flag    # separate — higher severity

    flagged = df["laundering_flag"].sum()
    logger.info(f"[Laundering Detector] Flagged {flagged} rows "
                f"(ratio threshold: {RATIO_THRESHOLD}x). "
                f"Minor-specific: {minor_flag.sum()}")
    return df
