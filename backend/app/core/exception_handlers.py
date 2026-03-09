"""Global exception handlers — converts exceptions to consistent HTTP JSON responses."""

import uuid
from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import (
    DataError,
    InterfaceError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError as SA_TimeoutError,
)
import logging

from app.core.config import settings
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


def _inject_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """
    Inject CORS headers into error responses.

    ServerErrorMiddleware sits above CORSMiddleware, so its responses bypass
    header injection — this ensures CORS headers are always present.
    """
    origin = request.headers.get("origin")
    if origin and origin in settings.BACKEND_CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: dict = None,
) -> JSONResponse:
    """Build a standardised error response envelope."""
    content = {"error": {"code": error_code, "message": message}}
    if details:
        content["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=content)


async def amstar_exception_handler(request: Request, exc: AmStarException) -> JSONResponse:
    """Map AmStar domain exceptions to HTTP status codes."""
    status_code = status.HTTP_400_BAD_REQUEST

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

    logger.warning(
        "Business exception: %s - %s",
        exc.error_code,
        exc.message,
        extra={
            "error_code": exc.error_code,
            "error_message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=status_code,
        details=exc.details if exc.details else None,
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    """Convert Pydantic validation errors to the standard error envelope."""
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"], "type": e["type"]}
        for e in exc.errors()
    ]

    logger.warning(
        "Validation error on %s",
        request.url.path,
        extra={"errors": errors, "path": request.url.path, "method": request.method},
    )

    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors},
    )


async def data_error_handler(request: Request, exc: DataError) -> JSONResponse:
    """
    Handle SQLAlchemy DataError → HTTP 400.

    Covers type mismatches, numeric overflow, and value-too-long errors raised
    by PostgreSQL. These are client errors, not infrastructure failures.
    """
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", "unknown")

    _pgcode_hints = {
        "22P02": "Invalid text representation (enum/type mismatch).",
        "22003": "Numeric value out of range.",
        "22001": "String too long for column.",
        "22007": "Invalid datetime format.",
        "22008": "Datetime field overflow.",
    }
    hint = _pgcode_hints.get(pgcode, f"PostgreSQL DataError pgcode={pgcode}.")

    logger.warning(
        "DataError: invalid data [pgcode=%s]",
        pgcode,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "pgcode": pgcode,
            "hint": hint,
            "db_orig": str(orig)[:300],
        },
        exc_info=True,
    )

    response = create_error_response(
        error_code="INVALID_DATA_FORMAT",
        message="The request contains a value that is not accepted by the database.",
        status_code=status.HTTP_400_BAD_REQUEST,
        details={"hint": hint} if settings.ENVIRONMENT == "development" else None,
    )
    return _inject_cors_headers(response, request)


def _classify_db_error(exc: SQLAlchemyError) -> dict:
    """
    Classify a SQLAlchemy exception into a structured diagnostic dict.

    Returns keys: error_code, category, is_retryable, hint.
    """
    if isinstance(exc, SA_TimeoutError):
        return {
            "error_code": "DB_POOL_EXHAUSTED",
            "category": "pool_timeout",
            "is_retryable": False,
            "hint": "All DB connections busy. Check pool_size, slow queries, or connection leaks.",
        }

    orig = getattr(exc, "orig", None)
    orig_str = str(orig).lower() if orig else str(exc).lower()

    if isinstance(exc, OperationalError):
        pgcode = getattr(orig, "pgcode", None) if orig else None
        if pgcode:
            if pgcode == "57014":
                return {
                    "error_code": "DB_STATEMENT_TIMEOUT",
                    "category": "statement_timeout",
                    "is_retryable": False,
                    "hint": "Query exceeded statement_timeout. Optimise query or increase timeout.",
                }
            if pgcode == "53300":
                return {
                    "error_code": "DB_TOO_MANY_CONNECTIONS",
                    "category": "connection_limit",
                    "is_retryable": True,
                    "hint": "PostgreSQL max_connections reached. Reduce pool_size or add PgBouncer.",
                }
            if pgcode in ("28P01", "28000"):
                return {
                    "error_code": "DB_AUTH_FAILURE",
                    "category": "authentication",
                    "is_retryable": False,
                    "hint": "DB credentials rejected. Check password rotation or IAM token expiry.",
                }
            if pgcode in ("08006", "08001", "08004"):
                return {
                    "error_code": "DB_CONNECTION_FAILURE",
                    "category": "network",
                    "is_retryable": True,
                    "hint": "PostgreSQL refused or dropped the connection. Check pg_hba.conf and firewall.",
                }

        if any(kw in orig_str for kw in ("connection refused", "could not connect", "no route to host")):
            return {
                "error_code": "DB_UNREACHABLE",
                "category": "network",
                "is_retryable": True,
                "hint": "Cannot reach DB host. Check DNS, Security Groups, VPC routing.",
            }
        if any(kw in orig_str for kw in ("ssl", "certificate", "tls")):
            return {
                "error_code": "DB_SSL_ERROR",
                "category": "ssl_tls",
                "is_retryable": False,
                "hint": "TLS handshake failed. Check certificate expiry or SSL mode mismatch.",
            }
        if any(kw in orig_str for kw in (
            "server closed the connection unexpectedly",
            "connection reset by peer",
            "broken pipe",
            "connection was closed",
        )):
            return {
                "error_code": "DB_CONNECTION_DROPPED",
                "category": "stale_connection",
                "is_retryable": True,
                "hint": "Server closed idle connection. Ensure pool_pre_ping=True and pool_recycle.",
            }
        if any(kw in orig_str for kw in ("timeout", "timed out", "connect timeout")):
            return {
                "error_code": "DB_CONNECT_TIMEOUT",
                "category": "connect_timeout",
                "is_retryable": True,
                "hint": "TCP connect timeout. DB host may be overloaded or unreachable.",
            }

        return {
            "error_code": "DB_OPERATIONAL_ERROR",
            "category": "operational",
            "is_retryable": False,
            "hint": f"Unclassified OperationalError. orig={orig_str[:200]}",
        }

    if isinstance(exc, InterfaceError):
        return {
            "error_code": "DB_INTERFACE_ERROR",
            "category": "driver",
            "is_retryable": True,
            "hint": "Driver interface error (closed connection or cursor). Check session lifecycle.",
        }

    return {
        "error_code": "DB_ERROR",
        "category": "general",
        "is_retryable": False,
        "hint": f"SQLAlchemy {type(exc).__name__}. Review query or schema.",
    }


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy errors with full classification.

    Returns a safe message to the client; diagnostic details go to logs only.
    In development mode, a ``debug`` field with the error category is included.
    """
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    classification = _classify_db_error(exc)

    logger.error(
        "Database error [%s]",
        classification["error_code"],
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "db_error_code": classification["error_code"],
            "db_category": classification["category"],
            "db_is_retryable": classification["is_retryable"],
            "db_hint": classification["hint"],
            "db_orig": str(getattr(exc, "orig", exc))[:500],
        },
        exc_info=True,
    )

    content: dict = {
        "error": {
            "code": classification["error_code"],
            "message": "A database error occurred. Please try again later.",
            "request_id": request_id,
        }
    }

    if settings.ENVIRONMENT == "development":
        content["error"]["debug"] = {
            "category": classification["category"],
            "is_retryable": classification["is_retryable"],
            "hint": classification["hint"],
        }

    response = JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=content,
        headers={"Retry-After": "5"} if classification["is_retryable"] else {},
    )
    return _inject_cors_headers(response, request)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    logger.error(
        "Unhandled exception: %s",
        type(exc).__name__,
        extra={"error": str(exc), "path": request.url.path, "method": request.method},
        exc_info=True,
    )
    response = create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    return _inject_cors_headers(response, request)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application."""
    app.add_exception_handler(AmStarException, amstar_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(DataError, data_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
