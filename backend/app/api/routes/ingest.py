import uuid, time, io, logging
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.services.preprocessor import run_pipeline_from_dataframes
from app.services.anomaly_engine import score_and_flag
from app.services.decision_logic import run_tri_shield, route
from app.schemas.enrollment import (
    IngestResponse, RedFlagItem, AnalysisSummary, ModuleBreakdown,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _cap_rows(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Sample down to MAX_ROWS_PER_CSV if the file is too large."""
    cap = settings.MAX_ROWS_PER_CSV
    if cap and len(df) > cap:
        logger.info(f"[{label}] {len(df)} rows → sampling {cap} (random, preserving distribution)")
        return df.sample(n=cap, random_state=42).reset_index(drop=True)
    return df


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    enrol_file: UploadFile = File(...),
    bio_file:   UploadFile = File(...),
    demo_file:  UploadFile = File(...),
):
    """
    Upload all three CSVs in one request.
    Returns the full list of red flags and a summary.
    """
    t0 = time.time()
    batch_id = str(uuid.uuid4())[:8]

    try:
        enrol = pd.read_csv(io.BytesIO(await enrol_file.read()))
        bio   = pd.read_csv(io.BytesIO(await bio_file.read()))
        demo  = pd.read_csv(io.BytesIO(await demo_file.read()))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    original_sizes = (len(enrol), len(bio), len(demo))
    enrol = _cap_rows(enrol, "enrol")
    bio   = _cap_rows(bio,   "bio")
    demo  = _cap_rows(demo,  "demo")
    logger.info(
        f"[{batch_id}] Input sizes: enrol={original_sizes[0]}, bio={original_sizes[1]}, "
        f"demo={original_sizes[2]} → capped to {len(enrol)}, {len(bio)}, {len(demo)}"
    )

    try:
        df, X_scaled = run_pipeline_from_dataframes(enrol, bio, demo)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Preprocessing failed: {e}")

    df = run_tri_shield(df)
    scores, flags = score_and_flag(X_scaled)
    result = route(df, scores, flags)

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    ghost_count = sum(
        1 for f in result["red_flags"]
        if "ghost_scanner" in f.get("modules_triggered", "")
    )
    migration_count = sum(
        1 for f in result["red_flags"]
        if "migration_radar" in f.get("modules_triggered", "")
    )
    laundering_count = sum(
        1 for f in result["red_flags"]
        if "laundering_detector" in f.get("modules_triggered", "")
    )

    red_flag_items = [RedFlagItem(**f) for f in result["red_flags"]]

    logger.info(
        f"[{batch_id}] Processed {result['secure_count'] + result['flagged_count']} rows "
        f"in {elapsed_ms}ms — {result['flagged_count']} flagged"
    )

    return IngestResponse(
        status="complete",
        batch_id=batch_id,
        summary=AnalysisSummary(
            total_records=result["secure_count"] + result["flagged_count"],
            flagged_count=result["flagged_count"],
            secure_count=result["secure_count"],
            module_breakdown=ModuleBreakdown(
                ghost_scanner=ghost_count,
                migration_radar=migration_count,
                laundering_detector=laundering_count,
            ),
            processing_time_ms=elapsed_ms,
        ),
        red_flags=red_flag_items,
    )
