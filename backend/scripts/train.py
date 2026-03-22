"""
scripts/train.py
----------------
Run once to train the Isolation Forest on your full dataset.

Usage:
  python scripts/train.py \
    --enrol  data/api_data_aadhar_enrolment_0_500000.csv \
    --bio    data/api_data_aadhar_biometric_0_500000.csv \
    --demo   data/api_data_aadhar_demographic_0_500000.csv
"""

import argparse
import logging
import joblib
from pathlib import Path
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.preprocessor import run_pipeline
from app.core.config import settings


def train(enrol_path, bio_path, demo_path):
    logger.info("Running preprocessing pipeline (fit mode)...")
    df, X_scaled = run_pipeline(enrol_path, bio_path, demo_path, fit=True)

    logger.info(f"Training Isolation Forest on {X_scaled.shape[0]} rows, "
                f"{X_scaled.shape[1]} features...")

    model = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination=0.01,   # ~1% of records expected fraudulent
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    settings.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.MODEL_PATH)
    logger.info(f"Model saved to {settings.MODEL_PATH}")

    # Quick self-eval
    from app.services.anomaly_engine import score_and_flag
    scores, flags = score_and_flag(X_scaled)
    logger.info(
        f"Self-evaluation: {flags.sum()} flagged "
        f"({100*flags.mean():.2f}%) from training set"
    )
    logger.info("Training complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enrol", required=True)
    parser.add_argument("--bio",   required=True)
    parser.add_argument("--demo",  required=True)
    args = parser.parse_args()
    train(args.enrol, args.bio, args.demo)
