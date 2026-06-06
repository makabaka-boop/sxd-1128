from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.models.feeding_record import FeedingRecord
from app.schemas.feeding_record import FeedingRecordCreate


def get_feeding_record(db: Session, record_id: int) -> Optional[FeedingRecord]:
    return db.query(FeedingRecord).filter(FeedingRecord.id == record_id).first()


def get_feeding_records(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    feeder_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[FeedingRecord]:
    query = db.query(FeedingRecord)
    
    if pen_id:
        query = query.filter(FeedingRecord.pen_id == pen_id)
    if feeder_id:
        query = query.filter(FeedingRecord.feeder_id == feeder_id)
    if start_date:
        query = query.filter(FeedingRecord.feeding_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(FeedingRecord.feeding_time <= datetime.combine(end_date, datetime.max.time()))
    
    return query.order_by(FeedingRecord.feeding_time.desc()).offset(skip).limit(limit).all()


def create_feeding_record(db: Session, record_in: FeedingRecordCreate, feeder_id: int) -> FeedingRecord:
    db_record = FeedingRecord(
        **record_in.model_dump(),
        feeder_id=feeder_id,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def delete_feeding_record(db: Session, record_id: int) -> bool:
    db_record = get_feeding_record(db, record_id)
    if not db_record:
        return False
    db.delete(db_record)
    db.commit()
    return True
