from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "StudioBridge API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/StudioBridge"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/StudioBridge"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # TossPayments
    TOSS_CLIENT_KEY: Optional[str] = None
    TOSS_SECRET_KEY: Optional[str] = None
    TOSS_WEBHOOK_SECRET: Optional[str] = None

    # Frontend
    API_BASE_URL: Optional[str] = "http://localhost:8000"
    KAKAO_MAP_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
