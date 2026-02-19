"""
Global Exception Handlers for FastAPI

This module provides centralized exception handling, converting custom
exceptions to HTTP responses with consistent formatting.
"""

import uuid
from typing import Union
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import (
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


# ============================================================================
# STANDARD ERROR RESPONSE FORMAT
# ============================================================================


def _inject_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """
    Manually add CORS headers to error responses.

    Needed because ServerErrorMiddleware (which handles bare Exception handlers)
    sits above CORSMiddleware in the Starlette stack, so its responses never
    pass through CORSMiddleware's header injection.
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


def _classify_db_error(exc: SQLAlchemyError) -> dict:
    """
    Преобразует SQLAlchemy-исключение в структурированный диагностический словарь.

    Именно здесь решается проблема "Unknown": вместо одного обезличенного
    DATABASE_ERROR мы выясняем реальную причину по цепочке признаков.

    Возвращает dict с ключами:
      error_code   — машиночитаемый код для логов / алертов
      category     — группа причины (pool / network / ssl / auth / timeout / driver)
      is_retryable — можно ли ретраить этот класс ошибок
      hint         — краткое описание для инженера дежурного (не для клиента)
    """
    # -----------------------------------------------------------------------
    # 1. Pool exhaustion — sqlalchemy.exc.TimeoutError
    #    Возникает, когда pool_timeout истёк и свободного соединения нет.
    #    Первопричина: либо медленные запросы держат соединения, либо pool_size мал.
    # -----------------------------------------------------------------------
    if isinstance(exc, SA_TimeoutError):
        return {
            "error_code": "DB_POOL_EXHAUSTED",
            "category": "pool_timeout",
            "is_retryable": False,  # retry только создаст очередь поверх очереди
            "hint": "All DB connections are busy. Check pool_size, slow queries, or connection leaks.",
        }

    orig = getattr(exc, "orig", None)
    orig_str = str(orig).lower() if orig else str(exc).lower()

    # -----------------------------------------------------------------------
    # 2. OperationalError — самый широкий класс; нужна детализация по orig
    # -----------------------------------------------------------------------
    if isinstance(exc, OperationalError):

        # 2a. Есть pgcode от PostgreSQL — точная классификация по SQLSTATE
        pgcode = getattr(orig, "pgcode", None) if orig else None
        if pgcode:
            # 57014 query_canceled: statement_timeout или lock_timeout сработал
            if pgcode == "57014":
                return {
                    "error_code": "DB_STATEMENT_TIMEOUT",
                    "category": "statement_timeout",
                    "is_retryable": False,
                    "hint": "Query exceeded statement_timeout. Optimize query or increase timeout.",
                }
            # 53300 too_many_connections: сервер отверг соединение
            if pgcode == "53300":
                return {
                    "error_code": "DB_TOO_MANY_CONNECTIONS",
                    "category": "connection_limit",
                    "is_retryable": True,
                    "hint": "PostgreSQL max_connections reached. Reduce pool_size or add PgBouncer.",
                }
            # 28P01 / 28000 authentication failure
            if pgcode in ("28P01", "28000"):
                return {
                    "error_code": "DB_AUTH_FAILURE",
                    "category": "authentication",
                    "is_retryable": False,
                    "hint": "DB credentials rejected. Check password rotation or IAM token expiry.",
                }
            # 08006 / 08001 connection_failure / sqlclient_unable_to_establish_sqlconnection
            if pgcode in ("08006", "08001", "08004"):
                return {
                    "error_code": "DB_CONNECTION_FAILURE",
                    "category": "network",
                    "is_retryable": True,
                    "hint": "PostgreSQL refused or dropped the connection. Check pg_hba.conf and firewall.",
                }

        # 2b. Нет pgcode — ошибка на уровне TCP/TLS до установки сессии
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
                "hint": "Server closed idle connection (NAT/FW timeout). Ensure pool_pre_ping=True and pool_recycle.",
            }
        if any(kw in orig_str for kw in ("timeout", "timed out", "connect timeout")):
            return {
                "error_code": "DB_CONNECT_TIMEOUT",
                "category": "connect_timeout",
                "is_retryable": True,
                "hint": "TCP connect timeout. DB host may be overloaded or unreachable.",
            }

        # Fallback для OperationalError без распознанного паттерна
        return {
            "error_code": "DB_OPERATIONAL_ERROR",
            "category": "operational",
            "is_retryable": False,
            "hint": f"Unclassified OperationalError. orig={orig_str[:200]}",
        }

    # -----------------------------------------------------------------------
    # 3. InterfaceError — ошибки psycopg2 драйвера (cursor/connection object)
    #    Обычно: использование закрытого соединения, stale cursor.
    # -----------------------------------------------------------------------
    if isinstance(exc, InterfaceError):
        return {
            "error_code": "DB_INTERFACE_ERROR",
            "category": "driver",
            "is_retryable": True,
            "hint": "Driver interface error (closed connection or cursor). Check session lifecycle.",
        }

    # -----------------------------------------------------------------------
    # 4. Все остальные SQLAlchemyError (IntegrityError, DataError, etc.)
    #    Не retryable — это ошибки данных или схемы, а не инфраструктуры.
    # -----------------------------------------------------------------------
    return {
        "error_code": "DB_ERROR",
        "category": "general",
        "is_retryable": False,
        "hint": f"SQLAlchemy {type(exc).__name__}. Review query or schema.",
    }


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors with full error classification.

    В логах теперь будет точная причина вместо "Unknown":
      - категория (network / pool_timeout / stale_connection / ssl / ...)
      - is_retryable: сигнал для alert-правил и авто-recovery
      - request_id: для корреляции с трейсами/метриками

    Клиенту возвращается только безопасное сообщение без внутренних деталей.
    В development-режиме добавляется поле `debug` с категорией.
    """
    # request_id для корреляции между логом и ответом клиента
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
            # orig доступен только для debugging; не отправляем клиенту
            "db_orig": str(getattr(exc, "orig", exc))[:500],
        },
        exc_info=True,
    )

    # Тело ответа клиенту: минимально, без внутренних деталей
    content: dict = {
        "error": {
            "code": classification["error_code"],
            "message": "A database error occurred. Please try again later.",
            "request_id": request_id,
        }
    }

    # В development добавляем категорию — удобно при локальной разработке
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

    response = create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return _inject_cors_headers(response, request)


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
