"""
preprocessor.py
---------------
Merges the three Aadhaar data feeds and produces a clean, scaled
NumPy feature matrix for the Isolation Forest.

Input CSVs (real column structure):
  Enrollment : date, state, district, pincode,
               age_0_5, age_5_17, age_18_greater
  Biometric  : date, state, district, pincode,
               bio_age_5_17, bio_age_17_
  Demographic: date, state, district, pincode,
               demo_age_5_17, demo_age_17_

Join key: (date, state, district, pincode)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import logging
from pathlib import Path
from typing import Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

JOIN_KEY = ["date", "state", "district", "pincode"]

# Final ML feature columns fed to Isolation Forest
FEATURE_COLS = [
    "state_enc",
    "district_enc",
    "pincode",
    "age_0_5",
    "age_5_17",
    "age_18_greater",
    "bio_age_5_17",
    "bio_age_17_",
    "demo_age_5_17",
    "demo_age_17_",
    "total_enrollments",
    "ghost_child_ratio",       # Module C — Ghost Scanner signal
    "bio_demo_ratio_5_17",     # Module B — Laundering Detector signal
    "bio_demo_ratio_17_",      # Module B — Laundering Detector signal
    "enrollment_velocity",     # Module A — Migration Radar signal
]


class PreprocessingError(Exception):
    pass


# ─────────────────────────────────────────────
# 1. LOAD
# ─────────────────────────────────────────────

def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    return df


# ─────────────────────────────────────────────
# 2. MERGE
# ─────────────────────────────────────────────

def merge_feeds(
    enrol: pd.DataFrame,
    bio: pd.DataFrame,
    demo: pd.DataFrame,
) -> pd.DataFrame:
    """
    Outer-join all three feeds on (date, state, district, pincode).
    Missing values after merge are filled with 0 — a district may have
    enrollment records but no biometric/demographic updates that day.
    """
    df = enrol.merge(bio, on=JOIN_KEY, how="outer")
    df = df.merge(demo, on=JOIN_KEY, how="outer")

    fill_cols = [
        "age_0_5", "age_5_17", "age_18_greater",
        "bio_age_5_17", "bio_age_17_",
        "demo_age_5_17", "demo_age_17_",
    ]
    df[fill_cols] = df[fill_cols].fillna(0).astype(int)
    return df


# ─────────────────────────────────────────────
# 3. CLEAN
# ─────────────────────────────────────────────

def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Parse date
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"])

    # Normalise state / district strings
    df["state"] = df["state"].str.strip().str.title()
    df["district"] = df["district"].str.strip().str.title()

    # Pincode sanity: 6-digit Indian pincodes
    df = df[df["pincode"].between(100000, 999999)]

    # Drop exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=JOIN_KEY)
    logger.info(f"Dropped {before - len(df)} duplicate (date,state,district,pincode) rows")

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────
# 4. FEATURE ENGINEERING
# ─────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derived features that directly power the three Tri-Shield modules:

    ghost_child_ratio    (Module C — Ghost Scanner)
      = age_0_5 / (total_enrollments + 1)
      High ratio at a pincode signals Ghost Children abuse.

    bio_demo_ratio_5_17  (Module B — Laundering Detector)
      = bio_age_5_17 / (demo_age_5_17 + 1)
      Disproportionate biometric vs demographic updates for minors
      = identity laundering signal.

    bio_demo_ratio_17_   (Module B — Laundering Detector)
      = bio_age_17_ / (demo_age_17_ + 1)
      Same for adults.

    enrollment_velocity  (Module A — Migration Radar)
      = rolling 30-day sum of total_enrollments per (state, district)
      Abnormal spikes indicate coordinated border-area enrollment.
    """
    df["total_enrollments"] = df["age_0_5"] + df["age_5_17"] + df["age_18_greater"]

    df["ghost_child_ratio"] = (
        df["age_0_5"] / (df["total_enrollments"] + 1)
    ).round(4)

    df["bio_demo_ratio_5_17"] = (
        df["bio_age_5_17"] / (df["demo_age_5_17"] + 1)
    ).round(4)

    df["bio_demo_ratio_17_"] = (
        df["bio_age_17_"] / (df["demo_age_17_"] + 1)
    ).round(4)

    # Enrollment velocity: rolling 30-day sum per district
    df = df.sort_values("date")
    df["enrollment_velocity"] = (
        df.groupby(["state", "district"])["total_enrollments"]
        .transform(lambda x: x.rolling(window=30, min_periods=1).sum())
    ).round(2)

    return df


# ─────────────────────────────────────────────
# 5. ENCODE CATEGORICALS
# ─────────────────────────────────────────────

def encode_categoricals(df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
    settings.ENCODER_DIR.mkdir(parents=True, exist_ok=True)

    for col in ["state", "district"]:
        enc_path = settings.ENCODER_DIR / f"{col}_encoder.pkl"
        out_col = f"{col}_enc"

        if fit or not enc_path.exists():
            le = LabelEncoder()
            df[out_col] = le.fit_transform(df[col].astype(str))
            joblib.dump(le, enc_path)
            logger.info(f"Fitted and saved encoder: {col} ({len(le.classes_)} classes)")
        else:
            le = joblib.load(enc_path)
            # Handle unseen labels: map to 0
            df[out_col] = df[col].apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else 0
            )

    return df


# ─────────────────────────────────────────────
# 6. SCALE
# ─────────────────────────────────────────────

def scale(
    df: pd.DataFrame,
    fit: bool = False,
) -> Tuple[pd.DataFrame, np.ndarray]:
    X = df[FEATURE_COLS].values.astype(float)

    if fit or not settings.SCALER_PATH.exists():
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        settings.SCALER_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(scaler, settings.SCALER_PATH)
        logger.info("Fitted and saved StandardScaler")
    else:
        scaler = joblib.load(settings.SCALER_PATH)
        X_scaled = scaler.transform(X)

    return df, X_scaled


# ─────────────────────────────────────────────
# 7. MASTER PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(
    enrol_path: str | Path,
    bio_path: str | Path,
    demo_path: str | Path,
    fit: bool = False,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Full pipeline from raw CSV paths to (DataFrame, scaled_matrix).

    Args:
        enrol_path: path to enrollment CSV
        bio_path:   path to biometric CSV
        demo_path:  path to demographic CSV
        fit:        True = fit+save scaler/encoders (training run)
                    False = load saved artefacts (inference)
    Returns:
        df       — merged DataFrame with all features + metadata
        X_scaled — float32 NumPy array (n_rows × len(FEATURE_COLS))
    """
    logger.info("Loading CSVs...")
    enrol = load_csv(enrol_path)
    bio   = load_csv(bio_path)
    demo  = load_csv(demo_path)

    logger.info("Merging feeds...")
    df = merge_feeds(enrol, bio, demo)

    logger.info("Cleaning...")
    df = clean(df)

    logger.info("Engineering features...")
    df = engineer_features(df)

    logger.info("Encoding categoricals...")
    df = encode_categoricals(df, fit=fit)

    logger.info("Scaling...")
    df, X_scaled = scale(df, fit=fit)

    logger.info(
        f"Pipeline complete: {len(df)} rows, {X_scaled.shape[1]} features. "
        f"Date range: {df['date'].min().date()} → {df['date'].max().date()}"
    )
    return df, X_scaled


# ─────────────────────────────────────────────
# 8. IN-MEMORY VARIANT (for FastAPI single-upload)
# ─────────────────────────────────────────────

def run_pipeline_from_dataframes(
    enrol: pd.DataFrame,
    bio: pd.DataFrame,
    demo: pd.DataFrame,
    fit: bool = False,
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Same pipeline but accepts DataFrames directly (API upload path)."""
    df = merge_feeds(enrol, bio, demo)
    df = clean(df)
    df = engineer_features(df)
    df = encode_categoricals(df, fit=fit)
    df, X_scaled = scale(df, fit=fit)
    return df, X_scaled
