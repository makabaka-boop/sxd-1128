from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.pen import Pen
from app.schemas.pen import PenCreate, PenUpdate


def get_pen(db: Session, pen_id: int) -> Optional[Pen]:
    return db.query(Pen).filter(Pen.id == pen_id).first()


def get_pen_by_name(db: Session, name: str) -> Optional[Pen]:
    return db.query(Pen).filter(Pen.name == name).first()


def get_pens(db: Session, skip: int = 0, limit: int = 100) -> List[Pen]:
    return db.query(Pen).offset(skip).limit(limit).all()


def create_pen(db: Session, pen_in: PenCreate) -> Pen:
    db_pen = Pen(**pen_in.model_dump())
    db.add(db_pen)
    db.commit()
    db.refresh(db_pen)
    return db_pen


def update_pen(db: Session, pen_id: int, pen_in: PenUpdate) -> Optional[Pen]:
    db_pen = get_pen(db, pen_id)
    if not db_pen:
        return None
    
    update_data = pen_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_pen, field, value)
    
    db.commit()
    db.refresh(db_pen)
    return db_pen


def delete_pen(db: Session, pen_id: int) -> bool:
    db_pen = get_pen(db, pen_id)
    if not db_pen:
        return False
    db.delete(db_pen)
    db.commit()
    return True
