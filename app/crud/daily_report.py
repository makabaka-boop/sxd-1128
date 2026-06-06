from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_

from app.models.daily_report import DailyReport
from app.models.feeding_record import FeedingRecord
from app.models.inspection_record import InspectionRecord
from app.models.inspection_item import InspectionItem
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
        ExceptionReport.resolve_time >= start_dt,
        ExceptionReport.resolve_time <= end_dt
    ).scalar() or 0
    
    exception_pending_count = db.query(func.count(ExceptionReport.id)).filter(
        ExceptionReport.pen_id == pen_id,
        ExceptionReport.report_time <= end_dt,
        ExceptionReport.status != ExceptionStatus.RESOLVED
    ).scalar() or 0
    
    resolved_exceptions = db.query(ExceptionReport).filter(
        ExceptionReport.pen_id == pen_id,
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


def get_abnormal_inspection_stats(db: Session, report_date: date, pen_id: int) -> dict:
    start_dt = datetime.combine(report_date, datetime.min.time())
    end_dt = datetime.combine(report_date, datetime.max.time())
    
    abnormal_records = db.query(InspectionRecord).filter(
        InspectionRecord.pen_id == pen_id,
        InspectionRecord.result == False,
        InspectionRecord.inspection_time >= start_dt,
        InspectionRecord.inspection_time <= end_dt
    ).all()
    
    abnormal_inspection_count = len(abnormal_records)
    
    pending_abnormal_count = 0
    item_stats: Dict[int, dict] = {}
    
    for record in abnormal_records:
        item_id = record.inspection_item_id
        if item_id not in item_stats:
            item = db.query(InspectionItem).filter(InspectionItem.id == item_id).first()
            item_stats[item_id] = {
                "inspection_item_id": item_id,
                "inspection_item_name": item.name if item else "未知",
                "abnormal_count": 0,
                "pending_count": 0
            }
        item_stats[item_id]["abnormal_count"] += 1
        
        has_pending_exception = db.query(ExceptionReport).filter(
            ExceptionReport.inspection_record_id == record.id,
            ExceptionReport.status != ExceptionStatus.RESOLVED
        ).first() is not None
        
        if has_pending_exception:
            item_stats[item_id]["pending_count"] += 1
            pending_abnormal_count += 1
    
    abnormal_items = sorted(item_stats.values(), key=lambda x: x["abnormal_count"], reverse=True)
    
    return {
        "abnormal_inspection_count": abnormal_inspection_count,
        "pending_abnormal_count": pending_abnormal_count,
        "abnormal_items": abnormal_items
    }


def get_all_pens_abnormal_stats(db: Session, report_date: date) -> List[dict]:
    pens = db.query(Pen).all()
    result = []
    for pen in pens:
        stats = get_abnormal_inspection_stats(db, report_date, pen.id)
        result.append({
            "pen_id": pen.id,
            "pen_name": pen.name,
            **stats
        })
    return result


def generate_daily_report(db: Session, report_date: date, pen_id: int, allow_overwrite_history: bool = False) -> DailyReport:
    existing = get_daily_report_by_date_and_pen(db, report_date, pen_id)
    
    if existing and not allow_overwrite_history and report_date < date.today():
        return existing
    
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


def get_date_range(report_date: date, comparison_type: str) -> Tuple[date, date, date, date]:
    if comparison_type == "day":
        curr_start = report_date
        curr_end = report_date
        prev_start = report_date - timedelta(days=1)
        prev_end = report_date - timedelta(days=1)
    elif comparison_type == "week":
        weekday = report_date.weekday()
        curr_start = report_date - timedelta(days=weekday)
        curr_end = report_date
        duration_days = (curr_end - curr_start).days
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=duration_days)
    elif comparison_type == "month":
        curr_start = report_date.replace(day=1)
        curr_end = report_date
        if curr_start.month == 1:
            prev_month_start = curr_start.replace(year=curr_start.year - 1, month=12)
        else:
            prev_month_start = curr_start.replace(month=curr_start.month - 1)
        duration_days = (curr_end - curr_start).days
        prev_start = prev_month_start
        prev_end = prev_start + timedelta(days=duration_days)
        import calendar
        last_day_prev = calendar.monthrange(prev_start.year, prev_start.month)[1]
        if prev_end.day > last_day_prev:
            prev_end = prev_end.replace(day=last_day_prev)
    else:
        curr_start = report_date
        curr_end = report_date
        prev_start = report_date - timedelta(days=1)
        prev_end = report_date - timedelta(days=1)
    
    return curr_start, curr_end, prev_start, prev_end


def aggregate_reports_in_range(db: Session, start_date: date, end_date: date, pen_id: Optional[int] = None) -> dict:
    query = db.query(DailyReport).filter(
        DailyReport.report_date >= start_date,
        DailyReport.report_date <= end_date
    )
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
    total_pass = sum(r.inspection_pass_count for r in reports)
    
    processing_hours_list = [r.avg_processing_hours for r in reports if r.avg_processing_hours is not None]
    avg_processing = round(sum(processing_hours_list) / len(processing_hours_list), 2) if processing_hours_list else 0
    
    exception_rate = round((total_exception / total_inspection * 100), 2) if total_inspection > 0 else 0
    pass_rate = round((total_pass / total_inspection * 100), 2) if total_inspection > 0 else 0
    
    return {
        "feeding_count": total_feeding,
        "exception_count": total_exception,
        "exception_rate": exception_rate,
        "avg_processing_hours": avg_processing,
        "inspection_pass_rate": pass_rate,
        "unfinished_items": total_unfinished,
    }


def get_report_comparison(
    db: Session,
    report_date: date,
    pen_id: Optional[int] = None,
    comparison_type: str = "day"
) -> dict:
    curr_start, curr_end, prev_start, prev_end = get_date_range(report_date, comparison_type)
    
    current = aggregate_reports_in_range(db, curr_start, curr_end, pen_id)
    previous = aggregate_reports_in_range(db, prev_start, prev_end, pen_id)
    
    result = {
        "report_date": report_date,
        "pen_id": pen_id,
        "current_period_start": curr_start,
        "current_period_end": curr_end,
        "previous_period_start": prev_start,
        "previous_period_end": prev_end,
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
