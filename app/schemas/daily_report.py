from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class AbnormalInspectionItem(BaseModel):
    inspection_item_id: int
    inspection_item_name: str
    abnormal_count: int
    pending_count: int


class PenInspectionStats(BaseModel):
    pen_id: int
    pen_name: str
    abnormal_inspection_count: int
    pending_abnormal_count: int
    abnormal_items: List[AbnormalInspectionItem]


class DailyReportBase(BaseModel):
    report_date: date
    pen_id: int
    feeding_count: int = 0
    total_feed_amount: float = 0
    inspection_count: int = 0
    inspection_pass_count: int = 0
    exception_count: int = 0
    exception_resolved_count: int = 0
    exception_pending_count: int = 0
    avg_processing_hours: Optional[float] = None
    unfinished_items: int = 0


class DailyReportResponse(DailyReportBase):
    id: int
    created_at: datetime
    pen_name: Optional[str] = None
    exception_rate: Optional[float] = None
    inspection_pass_rate: Optional[float] = None
    abnormal_inspection_count: Optional[int] = None
    pending_abnormal_count: Optional[int] = None
    abnormal_items: Optional[List[AbnormalInspectionItem]] = None

    class Config:
        from_attributes = True


class ComparisonData(BaseModel):
    current_value: float
    previous_value: float
    change_rate: Optional[float] = None


class ReportComparison(BaseModel):
    report_date: date
    pen_id: Optional[int] = None
    pen_name: Optional[str] = None
    current_period_start: Optional[date] = None
    current_period_end: Optional[date] = None
    previous_period_start: Optional[date] = None
    previous_period_end: Optional[date] = None
    
    feeding_count: Optional[ComparisonData] = None
    exception_count: Optional[ComparisonData] = None
    exception_rate: Optional[ComparisonData] = None
    avg_processing_hours: Optional[ComparisonData] = None
    inspection_pass_rate: Optional[ComparisonData] = None
    unfinished_items: Optional[ComparisonData] = None


class DailyReport(DailyReportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
