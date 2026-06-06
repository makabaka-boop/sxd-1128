from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InspectionRecordBase(BaseModel):
    pen_id: int
    inspection_item_id: int
    result: bool
    remark: Optional[str] = None
    inspection_time: datetime


class InspectionExceptionData(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    severity: str = Field(default="normal")
    description: str = Field(..., min_length=1)


class InspectionRecordCreate(InspectionRecordBase):
    exception_data: Optional[InspectionExceptionData] = None


class InspectionRecordResponse(InspectionRecordBase):
    id: int
    inspector_id: int
    created_at: datetime
    pen_name: Optional[str] = None
    inspector_name: Optional[str] = None
    inspection_item_name: Optional[str] = None

    class Config:
        from_attributes = True


class InspectionRecord(InspectionRecordBase):
    id: int
    inspector_id: int
    created_at: datetime

    class Config:
        from_attributes = True
