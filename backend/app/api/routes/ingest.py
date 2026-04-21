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

    logger.info(
        f"[{batch_id}] Input sizes: enrol={len(enrol)}, bio={len(bio)}, demo={len(demo)}"
    )

    try:
        # Row-cap is applied AFTER merge inside the pipeline so that all
        # three feeds stay aligned on (date, state, district, pincode).
        df, X_scaled = run_pipeline_from_dataframes(
            enrol, bio, demo,
            max_rows=settings.MAX_ROWS_PER_CSV or None,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Preprocessing failed: {e}")

    df = run_tri_shield(df)
    scores, flags = score_and_flag(X_scaled)
    result = route(df, scores, flags)

    elapsed_ms = round((time.time() - t0) * 1000, 1)

    # Every flagged row is placed into exactly ONE "primary" bucket (for
    # the headline breakdown) based on the highest-priority module that
    # fired — so ghost + laundering + migration + isolation_forest_only
    # always sums to flagged_count.
    #
    # We also keep a raw "any-module" count per rule so analysts can see
    # how many records each detector independently caught.
    ghost_any = sum(1 for f in result["red_flags"] if "ghost_scanner"        in f.get("modules_triggered", ""))
    laund_any = sum(1 for f in result["red_flags"] if "laundering_detector"  in f.get("modules_triggered", ""))
    migr_any  = sum(1 for f in result["red_flags"] if "migration_radar"      in f.get("modules_triggered", ""))

    isolation_only   = 0
    multi_module     = 0
    for f in result["red_flags"]:
        mods = [m for m in f.get("modules_triggered", "").split(",") if m and m != "isolation_forest_only"]
        if len(mods) == 0:
            isolation_only += 1
        elif len(mods) >= 2:
            multi_module += 1

    red_flag_items = [RedFlagItem(**f) for f in result["red_flags"]]

    logger.info(
        f"[{batch_id}] Processed {result['secure_count'] + result['flagged_count']} rows "
        f"in {elapsed_ms}ms — {result['flagged_count']} flagged "
        f"(ghost={ghost_any} laund={laund_any} migr={migr_any} "
        f"isolation_only={isolation_only} multi={multi_module})"
    )

    return IngestResponse(
        status="complete",
        batch_id=batch_id,
        summary=AnalysisSummary(
            total_records=result["secure_count"] + result["flagged_count"],
            flagged_count=result["flagged_count"],
            secure_count=result["secure_count"],
            module_breakdown=ModuleBreakdown(
                ghost_scanner=ghost_any,
                migration_radar=migr_any,
                laundering_detector=laund_any,
                isolation_forest_only=isolation_only,
                multi_module=multi_module,
            ),
            processing_time_ms=elapsed_ms,
        ),
        red_flags=red_flag_items,
    )
