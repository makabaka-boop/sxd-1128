from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import traceback

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.core.scheduler import start_scheduler, stop_scheduler
from app.crud.user import create_user, get_user_by_username
from app.schemas.user import UserCreate
from app.models.user import UserRole

from app.api import auth, users, pens, inspection_items, inspection_records, feeding_records, exceptions, daily_reports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    Base.metadata.create_all(bind=engine)


def create_default_admin():
    db = SessionLocal()
    try:
        admin = get_user_by_username(db, "admin")
        if not admin:
            admin_create = UserCreate(
                username="admin",
                full_name="系统管理员",
                password="admin123",
                role=UserRole.ADMIN
            )
            create_user(db, admin_create)
            logger.info("Default admin user created: username=admin, password=admin123")
        
        field_worker = get_user_by_username(db, "worker")
        if not field_worker:
            worker_create = UserCreate(
                username="worker",
                full_name="现场人员",
                password="worker123",
                role=UserRole.FIELD_WORKER
            )
            create_user(db, worker_create)
            logger.info("Default field worker created: username=worker, password=worker123")
        
        observer = get_user_by_username(db, "observer")
        if not observer:
            observer_create = UserCreate(
                username="observer",
                full_name="观察员",
                password="observer123",
                role=UserRole.OBSERVER
            )
            create_user(db, observer_create)
            logger.info("Default observer created: username=observer, password=observer123")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    create_tables()
    create_default_admin()
    start_scheduler()
    yield
    logger.info("Shutting down application...")
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="养殖场管理系统 API - 栏区巡检、喂养记录、异常上报、日报汇总",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Uncaught exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = FastAPI(title="API v1")


@api_router.exception_handler(Exception)
async def api_exception_handler(request: Request, exc: Exception):
    logger.error(f"API Uncaught exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )


api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(pens.router, prefix="/pens", tags=["栏区管理"])
api_router.include_router(inspection_items.router, prefix="/inspection-items", tags=["巡检项管理"])
api_router.include_router(inspection_records.router, prefix="/inspection-records", tags=["巡检记录"])
api_router.include_router(feeding_records.router, prefix="/feeding-records", tags=["喂养记录"])
api_router.include_router(exceptions.router, prefix="/exceptions", tags=["异常上报"])
api_router.include_router(daily_reports.router, prefix="/daily-reports", tags=["日报报表"])

app.mount(settings.API_V1_STR, api_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "养殖场管理系统运行正常"}
