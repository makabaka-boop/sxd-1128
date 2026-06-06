from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.models.exception_report import ExceptionReport, ExceptionStatus
from app.schemas.exception_report import ExceptionReportCreate, ExceptionReportUpdate


def get_exception_report(db: Session, report_id: int) -> Optional[ExceptionReport]:
    return db.query(ExceptionReport).filter(ExceptionReport.id == report_id).first()


def get_exception_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    reporter_id: Optional[int] = None,
    status: Optional[ExceptionStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[ExceptionReport]:
    query = db.query(ExceptionReport)
    
    if pen_id:
        query = query.filter(ExceptionReport.pen_id == pen_id)
    if reporter_id:
        query = query.filter(ExceptionReport.reporter_id == reporter_id)
    if status:
        query = query.filter(ExceptionReport.status == status)
    if start_date:
        query = query.filter(ExceptionReport.report_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(ExceptionReport.report_time <= datetime.combine(end_date, datetime.max.time()))
    
    return query.order_by(ExceptionReport.report_time.desc()).offset(skip).limit(limit).all()


def create_exception_report(db: Session, report_in: ExceptionReportCreate, reporter_id: int) -> ExceptionReport:
    db_report = ExceptionReport(
        **report_in.model_dump(),
        reporter_id=reporter_id,
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


def update_exception_report(db: Session, report_id: int, report_in: ExceptionReportUpdate) -> Optional[ExceptionReport]:
    db_report = get_exception_report(db, report_id)
    if not db_report:
        return None
    
    update_data = report_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_report, field, value)
    
    db.commit()
    db.refresh(db_report)
    return db_report


def delete_exception_report(db: Session, report_id: int) -> bool:
    db_report = get_exception_report(db, report_id)
    if not db_report:
        return False
    db.delete(db_report)
    db.commit()
    return True
