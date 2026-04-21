from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    # ── Isolation Forest threshold ──────────────────────────────
    # Scores below this from `decision_function` are treated as anomalies.
    # Tuned to ~-0.08 (stricter than the previous -0.05) so the IF layer
    # stays close to its trained contamination rate (~1%) on real data
    # and stops contributing excessive false positives.
    ANOMALY_THRESHOLD: float = -0.08

    # ── Tri-Shield thresholds ───────────────────────────────────
    # All three have been tightened to reduce false positives observed
    # on production uploads where ~3.5% of rows were being flagged.
    GHOST_CHILD_AGE_MAX: int = 5              # age_0_5 bucket (Ghost Scanner)
    MIGRATION_ZSCORE_THRESHOLD: float = 4.0   # was 3.0 — ±4σ is truly extreme
    LAUNDERING_BIO_DEMO_RATIO_THRESHOLD: float = 8.0   # was 5.0

    # ── Volume gate ─────────────────────────────────────────────
    # A (date, pincode) row must have at least this many enrollments to
    # be considered for flagging. Kills the "Andaman & Nicobar problem"
    # where sub-island pincodes record 2–3 enrollments a day and every
    # tiny fluctuation becomes a statistical outlier. Real fraud schemes
    # need volume to move the needle.
    MIN_TOTAL_ENROLLMENTS_TO_FLAG: int = 10

    # ── Paths ───────────────────────────────────────────────────
    MODEL_PATH: Path = Path("ml/model.pkl")
    SCALER_PATH: Path = Path("ml/scaler.pkl")
    ENCODER_DIR: Path = Path("ml/encoders")
    REPORTS_DIR: Path = Path("reports")

    # Cap rows per CSV to keep analysis fast (0 = no limit).
    # Note: cap is applied AFTER merging the three feeds so that the
    # (date, state, district, pincode) alignment is preserved — sampling
    # the raw CSVs independently used to break the join.
    MAX_ROWS_PER_CSV: int = 15000

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
