from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "StudioBridge API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/StudioBridge"
    DATABASE_URL_SYNC: str = "postgresql://postgres:password@localhost:5432/StudioBridge"

    # DB Connection Pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # TossPayments
    TOSS_CLIENT_KEY: Optional[str] = None
    TOSS_SECRET_KEY: Optional[str] = None
    TOSS_WEBHOOK_SECRET: Optional[str] = None

    # SMS Provider (CoolSMS)
    SMS_PROVIDER: str = "mock"              # mock | coolsms
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None
    SMS_SENDER_NUMBER: Optional[str] = None

    # 국세청 사업자등록정보 조회
    NTS_SERVICE_KEY: Optional[str] = None
    NTS_API_BASE_URL: str = "https://api.odcloud.kr/api/nts-businessman/v1"

    # Subscription auto-renewal
    CRON_SECRET: Optional[str] = None

    # Bank transfer (무통장입금)
    BANK_ACCOUNT_NUMBER: str = ""
    BANK_ACCOUNT_HOLDER: str = ""
    BANK_NAME: str = ""

    # File Upload
    STORAGE_BACKEND: str = "local"  # local / s3
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    UPLOAD_MAX_SIZE_MB: int = 10

    # Email
    EMAIL_PROVIDER: str = "mock"  # mock / smtp / sendgrid
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:8501",
        "http://localhost:3000",
    ]

    # Frontend
    API_BASE_URL: Optional[str] = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8501"
    KAKAO_MAP_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
