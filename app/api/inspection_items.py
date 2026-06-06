from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.api.deps import require_admin, require_business_data
from app.models.user import User
from app.crud.inspection_item import get_inspection_items, get_inspection_item, create_inspection_item, update_inspection_item, delete_inspection_item
from app.schemas.inspection_item import InspectionItem as InspectionItemSchema, InspectionItemCreate, InspectionItemUpdate

router = APIRouter()


@router.get("/", response_model=List[InspectionItemSchema])
def list_inspection_items(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_data)
):
    items = get_inspection_items(db, skip=skip, limit=limit, is_active=is_active)
    return items


@router.get("/{item_id}", response_model=InspectionItemSchema)
def get_inspection_item_by_id(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_business_data)
):
    item = get_inspection_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection item not found"
        )
    return item


@router.post("/", response_model=InspectionItemSchema, status_code=status.HTTP_201_CREATED)
def create_new_inspection_item(
    item_in: InspectionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    item = create_inspection_item(db, item_in)
    return item


@router.put("/{item_id}", response_model=InspectionItemSchema)
def update_existing_inspection_item(
    item_id: int,
    item_in: InspectionItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    item = update_inspection_item(db, item_id, item_in)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection item not found"
        )
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_inspection_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    success = delete_inspection_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection item not found"
        )
    return None
