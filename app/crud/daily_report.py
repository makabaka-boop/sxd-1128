from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_

from app.models.daily_report import DailyReport
from app.models.feeding_record import FeedingRecord
from app.models.inspection_record import InspectionRecord
from app.models.exception_report import ExceptionReport, ExceptionStatus
from app.models.pen import Pen


def get_daily_report(db: Session, report_id: int) -> Optional[DailyReport]:
    return db.query(DailyReport).filter(DailyReport.id == report_id).first()


def get_daily_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[DailyReport]:
    query = db.query(DailyReport)
    
    if pen_id:
        query = query.filter(DailyReport.pen_id == pen_id)
    if start_date:
        query = query.filter(DailyReport.report_date >= start_date)
    if end_date:
        query = query.filter(DailyReport.report_date <= end_date)
    
    return query.order_by(DailyReport.report_date.desc(), DailyReport.pen_id).offset(skip).limit(limit).all()


def get_daily_report_by_date_and_pen(db: Session, report_date: date, pen_id: int) -> Optional[DailyReport]:
    return db.query(DailyReport).filter(
        DailyReport.report_date == report_date,
        DailyReport.pen_id == pen_id
    ).first()


def calculate_daily_stats(db: Session, report_date: date, pen_id: int) -> dict:
    start_dt = datetime.combine(report_date, datetime.min.time())
    end_dt = datetime.combine(report_date, datetime.max.time())
    
    feeding_count = db.query(func.count(FeedingRecord.id)).filter(
        FeedingRecord.pen_id == pen_id,
        FeedingRecord.feeding_time >= start_dt,
        FeedingRecord.feeding_time <= end_dt
    ).scalar() or 0
    
    total_feed_amount = db.query(func.sum(FeedingRecord.feed_amount)).filter(
        FeedingRecord.pen_id == pen_id,
        FeedingRecord.feeding_time >= start_dt,
        FeedingRecord.feeding_time <= end_dt
    ).scalar() or 0
    
    inspection_count = db.query(func.count(InspectionRecord.id)).filter(
        InspectionRecord.pen_id == pen_id,
        InspectionRecord.inspection_time >= start_dt,
        InspectionRecord.inspection_time <= end_dt
    ).scalar() or 0
    
    inspection_pass_count = db.query(func.count(InspectionRecord.id)).filter(
        InspectionRecord.pen_id == pen_id,
        InspectionRecord.result == True,
        InspectionRecord.inspection_time >= start_dt,
        InspectionRecord.inspection_time <= end_dt
    ).scalar() or 0
    
    exception_count = db.query(func.count(ExceptionReport.id)).filter(
        ExceptionReport.pen_id == pen_id,
        ExceptionReport.report_time >= start_dt,
        ExceptionReport.report_time <= end_dt
    ).scalar() or 0
    
    exception_resolved_count = db.query(func.count(ExceptionReport.id)).filter(
        ExceptionReport.pen_id == pen_id,
        ExceptionReport.status == ExceptionStatus.RESOLVED,
        ExceptionReport.resolve_time >= start_dt,
        ExceptionReport.resolve_time <= end_dt
    ).scalar() or 0
    
    exception_pending_count = db.query(func.count(ExceptionReport.id)).filter(
        ExceptionReport.pen_id == pen_id,
        ExceptionReport.status.in_([ExceptionStatus.PENDING, ExceptionStatus.PROCESSING]),
        ExceptionReport.report_time <= end_dt
    ).scalar() or 0
    
    resolved_exceptions = db.query(ExceptionReport).filter(
        ExceptionReport.pen_id == pen_id,
        ExceptionReport.status == ExceptionStatus.RESOLVED,
        ExceptionReport.resolve_time >= start_dt,
        ExceptionReport.resolve_time <= end_dt
    ).all()
    
    avg_processing_hours = None
    if resolved_exceptions:
        total_hours = 0
        for exc in resolved_exceptions:
            if exc.report_time and exc.resolve_time:
                delta = exc.resolve_time - exc.report_time
                total_hours += delta.total_seconds() / 3600
        avg_processing_hours = round(total_hours / len(resolved_exceptions), 2)
    
    unfinished_items = exception_pending_count
    
    return {
        "report_date": report_date,
        "pen_id": pen_id,
        "feeding_count": feeding_count,
        "total_feed_amount": float(total_feed_amount),
        "inspection_count": inspection_count,
        "inspection_pass_count": inspection_pass_count,
        "exception_count": exception_count,
        "exception_resolved_count": exception_resolved_count,
        "exception_pending_count": exception_pending_count,
        "avg_processing_hours": avg_processing_hours,
        "unfinished_items": unfinished_items,
    }


def generate_daily_report(db: Session, report_date: date, pen_id: int) -> DailyReport:
    existing = get_daily_report_by_date_and_pen(db, report_date, pen_id)
    stats = calculate_daily_stats(db, report_date, pen_id)
    
    if existing:
        for key, value in stats.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_report = DailyReport(**stats)
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report


def generate_all_daily_reports(db: Session, report_date: Optional[date] = None) -> List[DailyReport]:
    if report_date is None:
        report_date = date.today()
    
    pens = db.query(Pen).all()
    reports = []
    for pen in pens:
        report = generate_daily_report(db, report_date, pen.id)
        reports.append(report)
    return reports


def calculate_change_rate(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def get_report_comparison(
    db: Session,
    report_date: date,
    pen_id: Optional[int] = None,
    comparison_type: str = "day"
) -> dict:
    if comparison_type == "day":
        prev_date = report_date - timedelta(days=1)
    elif comparison_type == "week":
        prev_date = report_date - timedelta(weeks=1)
    elif comparison_type == "month":
        prev_date = report_date - timedelta(days=30)
    else:
        prev_date = report_date - timedelta(days=1)
    
    def aggregate_reports(target_date: date) -> dict:
        query = db.query(DailyReport).filter(DailyReport.report_date == target_date)
        if pen_id:
            query = query.filter(DailyReport.pen_id == pen_id)
        reports = query.all()
        
        if not reports:
            return {
                "feeding_count": 0,
                "exception_count": 0,
                "exception_rate": 0,
                "avg_processing_hours": 0,
                "inspection_pass_rate": 0,
                "unfinished_items": 0,
            }
        
        total_feeding = sum(r.feeding_count for r in reports)
        total_exception = sum(r.exception_count for r in reports)
        total_inspection = sum(r.inspection_count for r in reports)
        total_unfinished = sum(r.unfinished_items for r in reports)
        
        processing_hours_list = [r.avg_processing_hours for r in reports if r.avg_processing_hours is not None]
        avg_processing = round(sum(processing_hours_list) / len(processing_hours_list), 2) if processing_hours_list else 0
        
        exception_rate = round((total_exception / total_inspection * 100), 2) if total_inspection > 0 else 0
        pass_rate = round((sum(r.inspection_pass_count for r in reports) / total_inspection * 100), 2) if total_inspection > 0 else 0
        
        return {
            "feeding_count": total_feeding,
            "exception_count": total_exception,
            "exception_rate": exception_rate,
            "avg_processing_hours": avg_processing,
            "inspection_pass_rate": pass_rate,
            "unfinished_items": total_unfinished,
        }
    
    current = aggregate_reports(report_date)
    previous = aggregate_reports(prev_date)
    
    result = {
        "report_date": report_date,
        "pen_id": pen_id,
    }
    
    for key in ["feeding_count", "exception_count", "exception_rate", "avg_processing_hours", "inspection_pass_rate", "unfinished_items"]:
        result[key] = {
            "current_value": current[key],
            "previous_value": previous[key],
            "change_rate": calculate_change_rate(current[key], previous[key]),
        }
    
    return result


def delete_daily_report(db: Session, report_id: int) -> bool:
    db_report = get_daily_report(db, report_id)
    if not db_report:
        return False
    db.delete(db_report)
    db.commit()
    return True
