"""
Global Exception Handlers for FastAPI

This module provides centralized exception handling, converting custom
exceptions to HTTP responses with consistent formatting.
"""

from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.exceptions import (
    AmStarException,
    AuthenticationError,
    InsufficientPermissionsError,
    ResourceNotFoundError,
    BusinessRuleViolationError,
    ValidationError as CustomValidationError,
    ExternalServiceError,
    RateLimitExceededError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# STANDARD ERROR RESPONSE FORMAT
# ============================================================================


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: dict = None
) -> JSONResponse:
    """
    Create a standardized error response

    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details (optional)

    Returns:
        JSONResponse with standardized error format
    """
    content = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(
        status_code=status_code,
        content=content
    )


# ============================================================================
# CUSTOM EXCEPTION HANDLERS
# ============================================================================


async def amstar_exception_handler(request: Request, exc: AmStarException) -> JSONResponse:
    """
    Handle all AmStar custom exceptions

    Maps custom exceptions to appropriate HTTP status codes
    """
    # Default to 400 Bad Request
    status_code = status.HTTP_400_BAD_REQUEST

    # Map exception types to HTTP status codes
    if isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, InsufficientPermissionsError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ResourceNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, RateLimitExceededError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, ExternalServiceError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    # Log error with context
    logger.warning(
        f"Business exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,  # Renamed from 'message' to avoid reserved key
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=status_code,
        details=exc.details if exc.details else None
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors

    Converts Pydantic validation errors to standardized format
    """
    errors = []

    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        }
    )

    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors}
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors

    Prevents database error details from leaking to clients
    """
    logger.error(
        "Database error",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )

    return create_error_response(
        error_code="DATABASE_ERROR",
        message="A database error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions

    Catches all unhandled exceptions to prevent server crashes
    """
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )

    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# ============================================================================
# REGISTER EXCEPTION HANDLERS
# ============================================================================


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application

    This should be called during application startup

    Args:
        app: FastAPI application instance
    """
    # Custom business exceptions
    app.add_exception_handler(AmStarException, amstar_exception_handler)

    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
