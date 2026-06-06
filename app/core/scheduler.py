from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
import logging

from app.database import SessionLocal
from app.crud.daily_report import generate_all_daily_reports
from app.config import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def daily_report_generation_task():
    logger.info("Starting daily report generation task...")
    try:
        db = SessionLocal()
        try:
            today = date.today()
            reports = generate_all_daily_reports(db, today)
            logger.info(f"Generated {len(reports)} daily reports for {today}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error generating daily reports: {e}")


def start_scheduler():
    scheduler.add_job(
        daily_report_generation_task,
        trigger=CronTrigger(
            hour=settings.DAILY_REPORT_GENERATION_HOUR,
            minute=settings.DAILY_REPORT_GENERATION_MINUTE
        ),
        id="daily_report_generation",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started. Daily report generation task scheduled.")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")
