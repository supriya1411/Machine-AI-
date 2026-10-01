import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AURUM Service Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://aurum_user:aurum_password@localhost:5432/aurum_db"
    )
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        "postgresql://aurum_user:aurum_password@localhost:5432/aurum_db"
    )

    # JWT Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "aurum-service-intelligence-production-super-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

    # AI Service
    AI_API_KEY: str = os.getenv("AI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Risk Engine Default Weights
    RISK_WEIGHT_FAILURES: float = 0.25
    RISK_WEIGHT_MTBF_TREND: float = 0.20
    RISK_WEIGHT_ENVIRONMENTAL: float = 0.20
    RISK_WEIGHT_PM_COMPLIANCE: float = 0.15
    RISK_WEIGHT_CRITICALITY: float = 0.10
    RISK_WEIGHT_ACTIVE_ALERTS: float = 0.10

    # IoT Thresholds Default
    DEFAULT_TEMP_SAFE_MIN: float = 18.0
    DEFAULT_TEMP_SAFE_MAX: float = 24.0
    DEFAULT_TEMP_WARN_MIN: float = 15.0
    DEFAULT_TEMP_WARN_MAX: float = 28.0
    DEFAULT_TEMP_CRIT_MIN: float = 10.0
    DEFAULT_TEMP_CRIT_MAX: float = 35.0

    DEFAULT_HUMIDITY_SAFE_MIN: float = 40.0
    DEFAULT_HUMIDITY_SAFE_MAX: float = 60.0
    DEFAULT_HUMIDITY_WARN_MIN: float = 30.0
    DEFAULT_HUMIDITY_WARN_MAX: float = 70.0
    DEFAULT_HUMIDITY_CRIT_MIN: float = 20.0
    DEFAULT_HUMIDITY_CRIT_MAX: float = 85.0

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
