from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create any missing DB tables and connect to Redis on startup; disconnect on shutdown."""
    # create_all is a no-op for tables that already exist — safe to call every startup
    Base.metadata.create_all(bind=engine)
    redis_client.connect()
    yield
    redis_client.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Register exception handlers (must be done before middleware)
register_exception_handlers(app)

# Middleware registration order — IMPORTANT:
# Starlette processes middlewares in LIFO order (last added = outermost wrapper).
# To handle CORS preflight (OPTIONS) before any rate-limiting or security checks,
# CORS must be the LAST add_middleware call so it wraps everything else.
#
# Effective request pipeline:
#   Request → CORSMiddleware → RateLimitMiddleware → SecurityHeadersMiddleware → App
#
# When re-enabling the commented middlewares, keep them ABOVE the CORS block.

# Security headers — innermost; applied after routing
#app.add_middleware(
    #SecurityHeadersMiddleware,
    #enable_hsts=settings.ENVIRONMENT == "production",
#)

# Rate limiting — middle layer; OPTIONS preflight never reaches here (CORS short-circuits)
#app.add_middleware(
    #RateLimitMiddleware,
    #requests_per_minute=getattr(settings, 'RATE_LIMIT_REQUESTS', 100),
    #auth_requests_per_minute=getattr(settings, 'AUTH_RATE_LIMIT_REQUESTS', 5),
#)

# CORS — outermost; must be added last so it executes first on every request.
# This ensures preflight OPTIONS responses always carry Access-Control-* headers,
# preventing net::ERR_EMPTY_RESPONSE on cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router
app.include_router(api_router, prefix=settings.API_V1_STR)


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
