import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import ingest, reports, health

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Aadhaar DRISHTI backend...")
    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    settings.ENCODER_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Ready.")
    yield
    logger.info("Shutting down DRISHTI backend.")


app = FastAPI(
    title="Aadhaar DRISHTI",
    description="Proactive fraud detection for Aadhaar enrollment data",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — default includes local dev ports + any Vercel preview URL for
# this project. Override via the ALLOWED_ORIGINS env var (comma-separated)
# once you have the final production domain.
_default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
_extra_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
_allowed_origins = _default_origins + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    # Regex permits any `*.vercel.app` preview URL (works for the main
    # deployment and every PR preview without extra configuration).
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,  tags=["health"])
app.include_router(ingest.router,  prefix="/api/v1", tags=["ingest"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
