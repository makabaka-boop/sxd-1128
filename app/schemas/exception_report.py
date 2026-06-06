from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.exception_report import ExceptionStatus


class ExceptionReportBase(BaseModel):
    pen_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    severity: str = "normal"
    report_time: datetime


class ExceptionReportCreate(ExceptionReportBase):
    pass


class ExceptionReportUpdate(BaseModel):
    status: Optional[ExceptionStatus] = None
    handler_id: Optional[int] = None
    resolve_time: Optional[datetime] = None
    resolution: Optional[str] = None


class ExceptionReportResponse(ExceptionReportBase):
    id: int
    reporter_id: int
    handler_id: Optional[int] = None
    status: ExceptionStatus
    resolve_time: Optional[datetime] = None
    resolution: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    pen_name: Optional[str] = None
    reporter_name: Optional[str] = None
    handler_name: Optional[str] = None
    processing_hours: Optional[float] = None

    class Config:
        from_attributes = True


class ExceptionReport(ExceptionReportBase):
    id: int
    reporter_id: int
    handler_id: Optional[int] = None
    status: ExceptionStatus
    resolve_time: Optional[datetime] = None
    resolution: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
