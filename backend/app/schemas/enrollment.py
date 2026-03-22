from pydantic import BaseModel
from typing import Optional


class RedFlagItem(BaseModel):
    date: str
    state: str
    district: str
    pincode: int
    age_0_5: int
    age_5_17: int
    age_18_greater: int
    bio_age_5_17: int
    bio_age_17_: int
    demo_age_5_17: int
    demo_age_17_: int
    total_enrollments: int
    ghost_child_ratio: float
    bio_demo_ratio_5_17: float
    bio_demo_ratio_17_: float
    enrollment_velocity: float
    anomaly_score: float
    modules_triggered: str
    severity: str
    migration_zscore: Optional[float] = 0.0
    ghost_child_zscore: Optional[float] = 0.0


class ModuleBreakdown(BaseModel):
    ghost_scanner: int
    migration_radar: int
    laundering_detector: int


class AnalysisSummary(BaseModel):
    total_records: int
    flagged_count: int
    secure_count: int
    module_breakdown: ModuleBreakdown
    processing_time_ms: float


class IngestResponse(BaseModel):
    status: str
    batch_id: str
    summary: AnalysisSummary
    red_flags: list[RedFlagItem]


class ReportRequest(BaseModel):
    date: Optional[str] = ""
    state: Optional[str] = ""
    district: Optional[str] = ""
    pincode: Optional[int] = 0
    severity: Optional[str] = "MEDIUM"
    anomaly_score: Optional[float] = 0.0
    modules_triggered: Optional[str] = ""
    ghost_child_ratio: Optional[float] = 0.0
    bio_demo_ratio_17_: Optional[float] = 0.0
    bio_demo_ratio_5_17: Optional[float] = 0.0
    enrollment_velocity: Optional[float] = 0.0
    migration_zscore: Optional[float] = 0.0
    age_0_5: Optional[int] = 0
    age_5_17: Optional[int] = 0
    age_18_greater: Optional[int] = 0
    bio_age_5_17: Optional[int] = 0
    bio_age_17_: Optional[int] = 0
    demo_age_5_17: Optional[int] = 0
    demo_age_17_: Optional[int] = 0
    total_enrollments: Optional[int] = 0
