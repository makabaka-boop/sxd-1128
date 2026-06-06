from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import io
import pandas as pd

from app.database import get_db
from app.api.deps import require_admin, require_report_viewer
from app.models.user import User
from app.crud.daily_report import (
    get_daily_reports,
    get_daily_report,
    generate_all_daily_reports,
    get_report_comparison,
)
from app.crud.pen import get_pen
from app.schemas.daily_report import DailyReport as DailyReportSchema, DailyReportResponse, ReportComparison

router = APIRouter()


@router.get("/", response_model=List[DailyReportResponse])
def list_daily_reports(
    skip: int = 0,
    limit: int = 100,
    pen_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_report_viewer)
):
    reports = get_daily_reports(
        db, skip=skip, limit=limit, pen_id=pen_id,
        start_date=start_date, end_date=end_date
    )
    result = []
    for report in reports:
        report_dict = report.__dict__.copy()
        if report.pen:
            report_dict["pen_name"] = report.pen.name
        if report.inspection_count > 0:
            report_dict["exception_rate"] = round((report.exception_count / report.inspection_count) * 100, 2)
            report_dict["inspection_pass_rate"] = round((report.inspection_pass_count / report.inspection_count) * 100, 2)
        else:
            report_dict["exception_rate"] = None
            report_dict["inspection_pass_rate"] = None
        result.append(report_dict)
    return result


@router.get("/{report_id}", response_model=DailyReportResponse)
def get_daily_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_report_viewer)
):
    report = get_daily_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily report not found"
        )
    report_dict = report.__dict__.copy()
    if report.pen:
        report_dict["pen_name"] = report.pen.name
    if report.inspection_count > 0:
        report_dict["exception_rate"] = round((report.exception_count / report.inspection_count) * 100, 2)
        report_dict["inspection_pass_rate"] = round((report.inspection_pass_count / report.inspection_count) * 100, 2)
    else:
        report_dict["exception_rate"] = None
        report_dict["inspection_pass_rate"] = None
    return report_dict


@router.post("/generate", response_model=List[DailyReportSchema])
def generate_reports(
    report_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    reports = generate_all_daily_reports(db, report_date)
    return reports


@router.get("/comparison/{comparison_type}", response_model=ReportComparison)
def get_comparison(
    comparison_type: str = Path(..., pattern="^(day|week|month)$"),
    report_date: Optional[date] = None,
    pen_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_report_viewer)
):
    if report_date is None:
        report_date = date.today()
    
    if pen_id:
        pen = get_pen(db, pen_id)
        if not pen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pen not found"
            )
    
    result = get_report_comparison(db, report_date, pen_id, comparison_type)
    
    if pen_id:
        pen = get_pen(db, pen_id)
        result["pen_name"] = pen.name if pen else None
    
    return result


@router.get("/export/excel")
def export_reports_excel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    pen_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_report_viewer)
):
    reports = get_daily_reports(
        db, skip=0, limit=10000, pen_id=pen_id,
        start_date=start_date, end_date=end_date
    )
    
    data = []
    for report in reports:
        exception_rate = None
        pass_rate = None
        if report.inspection_count > 0:
            exception_rate = round((report.exception_count / report.inspection_count) * 100, 2)
            pass_rate = round((report.inspection_pass_count / report.inspection_count) * 100, 2)
        
        data.append({
            "日期": report.report_date,
            "栏区": report.pen.name if report.pen else "未知",
            "喂养次数": report.feeding_count,
            "总喂养量": report.total_feed_amount,
            "巡检次数": report.inspection_count,
            "巡检通过次数": report.inspection_pass_count,
            "巡检通过率(%)": pass_rate,
            "异常数量": report.exception_count,
            "异常率(%)": exception_rate,
            "已解决异常": report.exception_resolved_count,
            "待处理异常": report.exception_pending_count,
            "平均处理时长(小时)": report.avg_processing_hours,
            "未完成项": report.unfinished_items,
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='日报汇总')
    
    output.seek(0)
    
    filename = f"daily_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
