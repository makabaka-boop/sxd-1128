from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class FeedingRecord(Base):
    __tablename__ = "feeding_records"

    id = Column(Integer, primary_key=True, index=True)
    pen_id = Column(Integer, ForeignKey("pens.id"), nullable=False)
    feeder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feed_type = Column(String(100), nullable=False)
    feed_amount = Column(Float, nullable=False)
    remark = Column(Text, nullable=True)
    feeding_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pen = relationship("Pen")
    feeder = relationship("User")
