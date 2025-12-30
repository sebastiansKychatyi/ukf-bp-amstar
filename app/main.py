"""
AmStar Football Platform - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the application
    """
    # Startup
    logger.info("Starting AmStar Football Platform API...")
    logger.info("Database connection pool initialized")

    yield

    # Shutdown
    logger.info("Shutting down AmStar Football Platform API...")
    logger.info("Closing database connections...")


# Create FastAPI application
app = FastAPI(
    title="AmStar Football Platform",
    description="""
    Backend API for organizing amateur football matches.

    ## Features

    * **Teams**: Create and manage football teams
    * **Players**: Track player profiles and statistics
    * **Join Requests**: Request/approval workflow for team membership
    * **Statistics**: Comprehensive match and player statistics
    * **Dynamic Ratings**: Automatic skill rating calculations

    ## Authentication

    Most endpoints require authentication via Bearer token.
    Register and login to obtain an access token.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Vue default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
# Uncomment when you implement these endpoints
# from app.api.endpoints import teams, statistics, players, auth

# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(teams.router, prefix="/api", tags=["Teams"])
# app.include_router(players.router, prefix="/api", tags=["Players"])
# app.include_router(statistics.router, prefix="/api", tags=["Statistics"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint - returns basic information
    """
    return {
        "message": "Welcome to AmStar Football Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": "amstar-api",
        "version": "1.0.0"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unexpected errors
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_type": type(exc).__name__
        }
    )


# Development endpoint - remove in production
@app.get("/debug/routes", tags=["Debug"], include_in_schema=False)
async def list_routes():
    """
    List all registered routes (for debugging)
    """
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return {"routes": routes}


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
