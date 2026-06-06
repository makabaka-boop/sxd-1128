from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InspectionRecord(Base):
    __tablename__ = "inspection_records"

    id = Column(Integer, primary_key=True, index=True)
    pen_id = Column(Integer, ForeignKey("pens.id"), nullable=False)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    inspection_item_id = Column(Integer, ForeignKey("inspection_items.id"), nullable=False)
    result = Column(Boolean, nullable=False)
    remark = Column(Text, nullable=True)
    inspection_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    pen = relationship("Pen")
    inspector = relationship("User")
    inspection_item = relationship("InspectionItem")
    exception_reports = relationship("ExceptionReport", back_populates="inspection_record")
