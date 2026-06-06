from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedingRecordBase(BaseModel):
    pen_id: int
    feed_type: str = Field(..., min_length=1, max_length=100)
    feed_amount: float = Field(..., gt=0)
    remark: Optional[str] = None
    feeding_time: datetime


class FeedingRecordCreate(FeedingRecordBase):
    pass


class FeedingRecordResponse(FeedingRecordBase):
    id: int
    feeder_id: int
    created_at: datetime
    pen_name: Optional[str] = None
    feeder_name: Optional[str] = None

    class Config:
        from_attributes = True


class FeedingRecord(FeedingRecordBase):
    id: int
    feeder_id: int
    created_at: datetime

    class Config:
        from_attributes = True
