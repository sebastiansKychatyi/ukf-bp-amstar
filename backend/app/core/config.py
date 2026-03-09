from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "AmStar Amateur Football Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/amstar_db"

    # Connection pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Timeouts (ms for PostgreSQL GUC params, s for connect_timeout)
    DB_CONNECT_TIMEOUT: int = 10
    DB_STATEMENT_TIMEOUT_MS: int = 30000
    DB_LOCK_TIMEOUT_MS: int = 10000
    DB_IDLE_IN_TX_TIMEOUT_MS: int = 60000

    # Retry
    DB_RETRY_MAX_ATTEMPTS: int = 3
    DB_RETRY_MIN_WAIT_S: float = 0.5
    DB_RETRY_MAX_WAIT_S: float = 10.0

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100       # requests per minute (global)
    AUTH_RATE_LIMIT_REQUESTS: int = 5    # requests per minute (auth endpoints)

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # Email (optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
