from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.api.deps import require_field_worker, require_observer, get_current_user
from app.models.user import User
from app.crud.inspection_record import get_inspection_records, get_inspection_record, create_inspection_record, delete_inspection_record
from app.crud.pen import get_pen
from app.crud.inspection_item import get_inspection_item
from app.schemas.inspection_record import InspectionRecord as InspectionRecordSchema, InspectionRecordCreate, InspectionRecordResponse

router = APIRouter()


@router.get("/", response_model=List[InspectionRecordResponse])
def list_inspection_records(
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    inspector_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer)
):
    records = get_inspection_records(
        db, skip=skip, limit=limit, pen_id=pen_id,
        inspector_id=inspector_id, start_date=start_date, end_date=end_date
    )
    result = []
    for record in records:
        record_dict = record.__dict__.copy()
        if record.pen:
            record_dict["pen_name"] = record.pen.name
        if record.inspector:
            record_dict["inspector_name"] = record.inspector.full_name
        if record.inspection_item:
            record_dict["inspection_item_name"] = record.inspection_item.name
        result.append(record_dict)
    return result


@router.get("/{record_id}", response_model=InspectionRecordResponse)
def get_inspection_record_by_id(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer)
):
    record = get_inspection_record(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection record not found"
        )
    record_dict = record.__dict__.copy()
    if record.pen:
        record_dict["pen_name"] = record.pen.name
    if record.inspector:
        record_dict["inspector_name"] = record.inspector.full_name
    if record.inspection_item:
        record_dict["inspection_item_name"] = record.inspection_item.name
    return record_dict


@router.post("/", response_model=InspectionRecordSchema, status_code=status.HTTP_201_CREATED)
def create_new_inspection_record(
    record_in: InspectionRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    pen = get_pen(db, record_in.pen_id)
    if not pen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pen not found"
        )
    item = get_inspection_item(db, record_in.inspection_item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection item not found"
        )
    record = create_inspection_record(db, record_in, inspector_id=current_user.id)
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_inspection_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    success = delete_inspection_record(db, record_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection record not found"
        )
    return None
