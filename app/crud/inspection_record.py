from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.models.inspection_record import InspectionRecord
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


def create_inspection_record(db: Session, record_in: InspectionRecordCreate, inspector_id: int) -> InspectionRecord:
    db_record = InspectionRecord(
        **record_in.model_dump(),
        inspector_id=inspector_id,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def delete_inspection_record(db: Session, record_id: int) -> bool:
    db_record = get_inspection_record(db, record_id)
    if not db_record:
        return False
    db.delete(db_record)
    db.commit()
    return True
