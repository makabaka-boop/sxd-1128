from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.api.deps import require_field_worker, require_business_data
from app.models.user import User
from app.crud.feeding_record import get_feeding_records, get_feeding_record, create_feeding_record, delete_feeding_record
from app.crud.pen import get_pen
from app.schemas.feeding_record import FeedingRecord as FeedingRecordSchema, FeedingRecordCreate, FeedingRecordResponse

router = APIRouter()


@router.get("/", response_model=List[FeedingRecordResponse])
def list_feeding_records(
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    feeder_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_data)
):
    records = get_feeding_records(
        db, skip=skip, limit=limit, pen_id=pen_id,
        feeder_id=feeder_id, start_date=start_date, end_date=end_date
    )
    result = []
    for record in records:
        record_dict = record.__dict__.copy()
        if record.pen:
            record_dict["pen_name"] = record.pen.name
        if record.feeder:
            record_dict["feeder_name"] = record.feeder.full_name
        result.append(record_dict)
    return result


@router.get("/{record_id}", response_model=FeedingRecordResponse)
def get_feeding_record_by_id(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_data)
):
    record = get_feeding_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feeding record not found"
        )
    record_dict = record.__dict__.copy()
    if record.pen:
        record_dict["pen_name"] = record.pen.name
    if record.feeder:
        record_dict["feeder_name"] = record.feeder.full_name
    return record_dict


@router.post("/", response_model=FeedingRecordSchema, status_code=status.HTTP_201_CREATED)
def create_new_feeding_record(
    record_in: FeedingRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    pen = get_pen(db, record_in.pen_id)
    if not pen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pen not found"
        )
    record = create_feeding_record(db, record_in, feeder_id=current_user.id)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_feeding_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    success = delete_feeding_record(db, record_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feeding record not found"
        )
    return None
