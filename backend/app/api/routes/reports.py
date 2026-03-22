"""
Stateless PDF report generation.
Accepts a red flag payload in the request body and returns a PDF.
"""

import logging
import uuid
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.schemas.enrollment import ReportRequest
from app.services.report_generator import generate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reports/generate")
async def generate_report(flag: ReportRequest):
    """Generate a PDF investigation report from a red flag payload."""
    report_id = str(uuid.uuid4())[:8]
    flag_dict = flag.model_dump()
    report_path = generate(flag_dict, report_id)
    logger.info(f"Report generated: {report_path}")
    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=f"drishti_report_{report_id}.pdf",
    )
