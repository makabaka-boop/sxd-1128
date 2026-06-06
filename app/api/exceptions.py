from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.api.deps import require_field_worker, require_observer, get_current_user
from app.models.user import User
from app.models.exception_report import ExceptionStatus
from app.crud.exception_report import get_exception_reports, get_exception_report, create_exception_report, update_exception_report, delete_exception_report
from app.crud.pen import get_pen
from app.crud.user import get_user
from app.schemas.exception_report import ExceptionReport as ExceptionReportSchema, ExceptionReportCreate, ExceptionReportUpdate, ExceptionReportResponse

router = APIRouter()


@router.get("/", response_model=List[ExceptionReportResponse])
def list_exception_reports(
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    reporter_id: Optional[int] = None,
    status: Optional[ExceptionStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer)
):
    reports = get_exception_reports(
        db, skip=skip, limit=limit, pen_id=pen_id,
        reporter_id=reporter_id, status=status,
        start_date=start_date, end_date=end_date
    )
    result = []
    for report in reports:
        report_dict = report.__dict__.copy()
        if report.pen:
            report_dict["pen_name"] = report.pen.name
        if report.reporter:
            report_dict["reporter_name"] = report.reporter.full_name
        if report.handler:
            report_dict["handler_name"] = report.handler.full_name
        if report.report_time and report.resolve_time:
            delta = report.resolve_time - report.report_time
            report_dict["processing_hours"] = round(delta.total_seconds() / 3600, 2)
        result.append(report_dict)
    return result


@router.get("/{report_id}", response_model=ExceptionReportResponse)
def get_exception_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_observer)
):
    report = get_exception_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception report not found"
        )
    report_dict = report.__dict__.copy()
    if report.pen:
        report_dict["pen_name"] = report.pen.name
    if report.reporter:
        report_dict["reporter_name"] = report.reporter.full_name
    if report.handler:
        report_dict["handler_name"] = report.handler.full_name
    if report.report_time and report.resolve_time:
        delta = report.resolve_time - report.report_time
        report_dict["processing_hours"] = round(delta.total_seconds() / 3600, 2)
    return report_dict


@router.post("/", response_model=ExceptionReportSchema, status_code=status.HTTP_201_CREATED)
def create_new_exception_report(
    report_in: ExceptionReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    pen = get_pen(db, report_in.pen_id)
    if not pen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pen not found"
        )
    report = create_exception_report(db, report_in, reporter_id=current_user.id)
    return report


@router.put("/{report_id}", response_model=ExceptionReportSchema)
def update_existing_exception_report(
    report_id: int,
    report_in: ExceptionReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    if report_in.handler_id:
        handler = get_user(db, report_in.handler_id)
        if not handler:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Handler user not found"
            )
    report = update_exception_report(db, report_id, report_in)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception report not found"
        )
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_exception_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_field_worker)
):
    success = delete_exception_report(db, report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception report not found"
        )
    return None
