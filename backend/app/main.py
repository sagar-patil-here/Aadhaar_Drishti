import logging
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,  tags=["health"])
app.include_router(ingest.router,  prefix="/api/v1", tags=["ingest"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
