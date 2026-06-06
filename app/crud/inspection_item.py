from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.inspection_item import InspectionItem
from app.schemas.inspection_item import InspectionItemCreate, InspectionItemUpdate


def get_inspection_item(db: Session, item_id: int) -> Optional[InspectionItem]:
    return db.query(InspectionItem).filter(InspectionItem.id == item_id).first()


def get_inspection_items(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[InspectionItem]:
    query = db.query(InspectionItem)
    if is_active is not None:
        query = query.filter(InspectionItem.is_active == is_active)
    return query.order_by(InspectionItem.sort_order, InspectionItem.id).offset(skip).limit(limit).all()


def create_inspection_item(db: Session, item_in: InspectionItemCreate) -> InspectionItem:
    db_item = InspectionItem(**item_in.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_inspection_item(db: Session, item_id: int, item_in: InspectionItemUpdate) -> Optional[InspectionItem]:
    db_item = get_inspection_item(db, item_id)
    if not db_item:
        return None
    
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_inspection_item(db: Session, item_id: int) -> bool:
    db_item = get_inspection_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True
