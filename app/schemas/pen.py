from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PenBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None


class PenCreate(PenBase):
    pass


class PenUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None


class Pen(PenBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
