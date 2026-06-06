from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import date, datetime

from app.models.inspection_record import InspectionRecord
from app.models.exception_report import ExceptionReport
from app.schemas.inspection_record import InspectionRecordCreate


def get_inspection_record(db: Session, record_id: int) -> Optional[InspectionRecord]:
    return db.query(InspectionRecord).filter(InspectionRecord.id == record_id).first()


def get_inspection_records(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    inspector_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[InspectionRecord]:
    query = db.query(InspectionRecord)
    
    if pen_id:
        query = query.filter(InspectionRecord.pen_id == pen_id)
    if inspector_id:
        query = query.filter(InspectionRecord.inspector_id == inspector_id)
    if start_date:
        query = query.filter(InspectionRecord.inspection_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(InspectionRecord.inspection_time <= datetime.combine(end_date, datetime.max.time()))
    
    return query.order_by(InspectionRecord.inspection_time.desc()).offset(skip).limit(limit).all()


def create_inspection_record(db: Session, record_in: InspectionRecordCreate, inspector_id: int) -> Tuple[InspectionRecord, Optional[ExceptionReport]]:
    record_data = record_in.model_dump(exclude={"exception_data"})
    db_record = InspectionRecord(
        **record_data,
        inspector_id=inspector_id,
    )
    db.add(db_record)
    db.flush()
    
    exception_report = None
    if not record_in.result and record_in.exception_data:
        exception_report = ExceptionReport(
            pen_id=record_in.pen_id,
            reporter_id=inspector_id,
            inspection_record_id=db_record.id,
            title=record_in.exception_data.title,
            description=record_in.exception_data.description,
            severity=record_in.exception_data.severity,
            report_time=record_in.inspection_time,
        )
        db.add(exception_report)
        db.flush()
    
    db.commit()
    db.refresh(db_record)
    if exception_report:
        db.refresh(exception_report)
    
    return db_record, exception_report


def delete_inspection_record(db: Session, record_id: int) -> bool:
    db_record = get_inspection_record(db, record_id)
    if not db_record:
        return False
    db.delete(db_record)
    db.commit()
    return True
