from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Isolation Forest threshold — scores below this are anomalies
    ANOMALY_THRESHOLD: float = -0.05

    # Tri-Shield thresholds
    GHOST_CHILD_AGE_MAX: int = 5           # age_0_5 bucket (Ghost Scanner)
    MIGRATION_ZSCORE_THRESHOLD: float = 3.0
    LAUNDERING_BIO_DEMO_RATIO_THRESHOLD: float = 5.0

    # Paths
    MODEL_PATH: Path = Path("ml/model.pkl")
    SCALER_PATH: Path = Path("ml/scaler.pkl")
    ENCODER_DIR: Path = Path("ml/encoders")
    REPORTS_DIR: Path = Path("reports")

    # Cap rows per CSV to keep analysis fast (0 = no limit)
    MAX_ROWS_PER_CSV: int = 15000

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
