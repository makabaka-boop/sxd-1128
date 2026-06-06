from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class ExceptionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"


class ExceptionReport(Base):
    __tablename__ = "exception_reports"

    id = Column(Integer, primary_key=True, index=True)
    pen_id = Column(Integer, ForeignKey("pens.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspection_record_id = Column(Integer, ForeignKey("inspection_records.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, default="normal")
    status = Column(Enum(ExceptionStatus), nullable=False, default=ExceptionStatus.PENDING)
    report_time = Column(DateTime(timezone=True), nullable=False)
    resolve_time = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    pen = relationship("Pen")
    reporter = relationship("User", foreign_keys=[reporter_id])
    handler = relationship("User", foreign_keys=[handler_id])
    inspection_record = relationship("InspectionRecord", back_populates="exception_reports")
