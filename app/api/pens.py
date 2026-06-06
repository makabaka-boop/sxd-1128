from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.api.deps import require_admin, require_business_data
from app.models.user import User
from app.crud.pen import get_pens, get_pen, get_pen_by_name, create_pen, update_pen, delete_pen
from app.schemas.pen import Pen as PenSchema, PenCreate, PenUpdate

router = APIRouter()


@router.get("/", response_model=List[PenSchema])
def list_pens(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_data)
):
    pens = get_pens(db, skip=skip, limit=limit)
    return pens


@router.get("/{pen_id}", response_model=PenSchema)
def get_pen_by_id(
    pen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_data)
):
    pen = get_pen(db, pen_id)
    if not pen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pen not found"
        )
    return pen


@router.post("/", response_model=PenSchema, status_code=status.HTTP_201_CREATED)
def create_new_pen(
    pen_in: PenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    existing_pen = get_pen_by_name(db, pen_in.name)
    if existing_pen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pen name already exists"
        )
    pen = create_pen(db, pen_in)
    return pen


@router.put("/{pen_id}", response_model=PenSchema)
def update_existing_pen(
    pen_id: int,
    pen_in: PenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    pen = update_pen(db, pen_id, pen_in)
    if not pen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pen not found"
        )
    return pen


@router.delete("/{pen_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_pen(
    pen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    success = delete_pen(db, pen_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pen not found"
        )
    return None
