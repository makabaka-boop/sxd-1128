from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "养殖场管理系统"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./farm_management.db"
    
    DAILY_REPORT_GENERATION_HOUR: int = 23
    DAILY_REPORT_GENERATION_MINUTE: int = 30
    
    class Config:
        case_sensitive = True


settings = Settings()
