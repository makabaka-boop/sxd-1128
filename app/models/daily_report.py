from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(Date, nullable=False, index=True)
    pen_id = Column(Integer, ForeignKey("pens.id"), nullable=False)
    
    feeding_count = Column(Integer, nullable=False, default=0)
    total_feed_amount = Column(Float, nullable=False, default=0)
    
    inspection_count = Column(Integer, nullable=False, default=0)
    inspection_pass_count = Column(Integer, nullable=False, default=0)
    
    exception_count = Column(Integer, nullable=False, default=0)
    exception_resolved_count = Column(Integer, nullable=False, default=0)
    exception_pending_count = Column(Integer, nullable=False, default=0)
    
    avg_processing_hours = Column(Float, nullable=True)
    unfinished_items = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pen = relationship("Pen")
