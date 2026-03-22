"""
anomaly_engine.py
-----------------
Loads the trained Isolation Forest and scores each row.

decision_function() returns a score per sample:
  - Negative score → anomaly (the more negative, the more anomalous)
  - Positive score → normal

We flip the sign so higher = more suspicious (intuitive for dashboards).
"""

import numpy as np
import joblib
import logging
from pathlib import Path
from sklearn.ensemble import IsolationForest
from typing import Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)

_model: IsolationForest | None = None


def load_model() -> IsolationForest:
    global _model
    if _model is None:
        if not settings.MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {settings.MODEL_PATH}. "
                "Run: python scripts/train.py first."
            )
        _model = joblib.load(settings.MODEL_PATH)
        logger.info(f"Isolation Forest loaded from {settings.MODEL_PATH}")
    return _model


def score(X_scaled: np.ndarray) -> np.ndarray:
    """
    Returns anomaly scores, shape (n_rows,).
    Higher value = MORE suspicious.
    Threshold is settings.ANOMALY_THRESHOLD (default -0.05).
    A row is flagged when raw decision_function score < threshold.
    """
    model = load_model()
    raw_scores = model.decision_function(X_scaled)   # negative = anomaly
    return raw_scores


def flag_mask(scores: np.ndarray) -> np.ndarray:
    """Boolean mask: True where score < threshold (i.e., flagged)."""
    return scores < settings.ANOMALY_THRESHOLD


def score_and_flag(X_scaled: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    scores = score(X_scaled)
    flags  = flag_mask(scores)
    logger.info(
        f"Scored {len(scores)} rows. "
        f"Flagged {flags.sum()} ({100*flags.mean():.2f}%)"
    )
    return scores, flags
