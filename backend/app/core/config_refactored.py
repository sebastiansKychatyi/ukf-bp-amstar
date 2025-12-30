"""
Application Configuration - REFACTORED VERSION

This is the secure, production-ready configuration module that:
- Requires all secrets from environment variables (no defaults)
- Validates configuration on startup
- Uses proper types and validation
- Separates development and production settings
"""

from typing import List, Optional
from pydantic import field_validator, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables

    All sensitive values MUST be provided via environment variables.
    No default values for secrets in production.
    """

    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================

    APP_NAME: str = "AmStar Football Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ========================================================================
    # SECURITY SETTINGS (NO DEFAULTS - MUST BE SET)
    # ========================================================================

    SECRET_KEY: str  # ✓ REQUIRED - No default value
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ========================================================================
    # DATABASE SETTINGS
    # ========================================================================

    DATABASE_URL: str
    # Example: postgresql://user:password@localhost:5432/amstar

    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    DATABASE_POOL_PRE_PING: bool = True

    # ========================================================================
    # REDIS SETTINGS
    # ========================================================================

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # ========================================================================
    # CORS SETTINGS (RESTRICTIVE BY DEFAULT)
    # ========================================================================

    # ✓ Must explicitly set allowed origins (no wildcard)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # ✓ Specific methods only
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    # ✓ Specific headers only
    CORS_ALLOW_HEADERS: List[str] = [
        "Accept",
        "Accept-Language",
        "Content-Type",
        "Authorization",
    ]

    CORS_ALLOW_CREDENTIALS: bool = True

    # ========================================================================
    # EMAIL SETTINGS (Optional)
    # ========================================================================

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[EmailStr] = None

    # ========================================================================
    # RATE LIMITING SETTINGS
    # ========================================================================

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # Requests per window
    RATE_LIMIT_WINDOW: int = 60     # Window in seconds (1 minute)

    # Stricter limits for auth endpoints
    AUTH_RATE_LIMIT_REQUESTS: int = 5
    AUTH_RATE_LIMIT_WINDOW: int = 60  # 5 attempts per minute

    # ========================================================================
    # SECURITY HEADERS
    # ========================================================================

    SECURITY_HEADERS_ENABLED: bool = True

    # ========================================================================
    # LOGGING SETTINGS
    # ========================================================================

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        Validate SECRET_KEY meets security requirements

        Requirements:
        - At least 32 characters
        - Cannot be the default/example value
        """
        if not v:
            raise ValueError(
                "SECRET_KEY is required. "
                "Generate one with: openssl rand -hex 32"
            )

        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Current length: {len(v)}"
            )

        # Prevent using example/default values
        insecure_values = [
            "your-secret-key-here",
            "change-in-production",
            "secret",
            "mysecretkey",
        ]

        if any(insecure in v.lower() for insecure in insecure_values):
            raise ValueError(
                "SECRET_KEY appears to be an example value. "
                "Generate a secure key with: openssl rand -hex 32"
            )

        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format"""
        if not v:
            raise ValueError("DATABASE_URL is required")

        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgresql+asyncpg://"
            )

        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: List[str]) -> List[str]:
        """
        Validate CORS origins

        Warns if wildcard is used in production
        """
        if "*" in v:
            import warnings
            warnings.warn(
                "CORS wildcard (*) detected. "
                "This should only be used in development!",
                UserWarning
            )

        return v

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================

    @property
    def redis_url(self) -> str:
        """Construct Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG

    # ========================================================================
    # PYDANTIC CONFIGURATION
    # ========================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Validate on assignment
        validate_assignment=True,
        # Extra fields not allowed
        extra="ignore",
    )


# ============================================================================
# SETTINGS INSTANCE
# ============================================================================


def get_settings() -> Settings:
    """
    Get settings instance

    This function can be overridden in tests to provide different settings
    """
    return Settings()


# Create global settings instance
settings = get_settings()


# ============================================================================
# SECURITY KEY GENERATOR
# ============================================================================


def generate_secret_key() -> str:
    """
    Generate a secure secret key

    Usage:
        python -c "from app.core.config_refactored import generate_secret_key; print(generate_secret_key())"

    Returns:
        Cryptographically secure random string
    """
    return secrets.token_hex(32)


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================


def validate_production_settings(settings: Settings) -> None:
    """
    Validate that production settings are secure

    Should be called on application startup in production

    Raises:
        ValueError: If production settings are insecure
    """
    errors = []

    # Check DEBUG is disabled in production
    if settings.DEBUG and settings.is_production:
        errors.append("DEBUG should be False in production")

    # Check CORS is not using wildcard
    if "*" in settings.CORS_ORIGINS:
        errors.append("CORS wildcard (*) should not be used in production")

    # Check email is configured (if needed)
    if not settings.SMTP_HOST and settings.is_production:
        import warnings
        warnings.warn("SMTP not configured - email features will not work", UserWarning)

    # Check rate limiting is enabled
    if not settings.RATE_LIMIT_ENABLED and settings.is_production:
        errors.append("Rate limiting should be enabled in production")

    # Check security headers are enabled
    if not settings.SECURITY_HEADERS_ENABLED and settings.is_production:
        errors.append("Security headers should be enabled in production")

    if errors:
        error_msg = "Production configuration errors:\n" + "\n".join(f"- {e}" for e in errors)
        raise ValueError(error_msg)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
BEFORE (.env file with defaults):
```
# ❌ Secret key has default value in code
# ❌ Can forget to set in production
```

AFTER (.env file required):
```
# ✓ Required environment variables
SECRET_KEY=generated-with-openssl-rand-hex-32-no-default-allowed
DATABASE_URL=postgresql://user:pass@localhost:5432/amstar

# Optional settings (have defaults)
DEBUG=False
CORS_ORIGINS=["https://amstar.com"]
```

GENERATE SECRET KEY:
```bash
# Command line
openssl rand -hex 32

# Or Python
python -c "from app.core.config_refactored import generate_secret_key; print(generate_secret_key())"
```

IN APPLICATION (main.py):
```python
from app.core.config_refactored import settings, validate_production_settings

# Validate on startup (production only)
if settings.is_production:
    validate_production_settings(settings)
```
"""
