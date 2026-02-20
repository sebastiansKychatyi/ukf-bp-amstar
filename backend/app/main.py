from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.redis import redis_client
from app.api.v1.router import api_router

# Import refactored components
from app.core.exception_handlers import register_exception_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

# Import Base + all models so create_all() sees every table
from app.db.base import Base  # noqa: F401 — side-effect import
from app.db.session import engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Register exception handlers (must be done before middleware)
register_exception_handlers(app)

# Add security headers middleware
#app.add_middleware(
    #SecurityHeadersMiddleware,
    #enable_hsts=settings.ENVIRONMENT == "production",
#)

# Add rate limiting middleware
#app.add_middleware(
    #RateLimitMiddleware,
    #requests_per_minute=getattr(settings, 'RATE_LIMIT_REQUESTS', 100),
    #auth_requests_per_minute=getattr(settings, 'AUTH_RATE_LIMIT_REQUESTS', 5),
#)

# CORS middleware (should be last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Create any missing DB tables, then connect to Redis."""
    # create_all is a no-op for tables that already exist — safe to call every startup
    Base.metadata.create_all(bind=engine)
    redis_client.connect()


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown"""
    redis_client.disconnect()


@app.get("/")
def root():
    return {
        "message": "Welcome to AmStar Amateur Football Platform API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
