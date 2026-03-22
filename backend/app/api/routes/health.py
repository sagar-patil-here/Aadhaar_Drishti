from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health():
    model_ready = settings.MODEL_PATH.exists()
    scaler_ready = settings.SCALER_PATH.exists()
    return {
        "status": "ok",
        "model_loaded": model_ready,
        "scaler_loaded": scaler_ready,
        "anomaly_threshold": settings.ANOMALY_THRESHOLD,
    }
