"""Database session management — hardened SQLAlchemy 2.0 + psycopg2 configuration."""

import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_db_url = settings.DATABASE_URL

# psycopg2 driver-level connection parameters
_connect_args = {
    # Fail fast if the DB host is unreachable instead of waiting for kernel timeout
    "connect_timeout": settings.DB_CONNECT_TIMEOUT,

    # TCP keepalives detect silently dropped connections (e.g. NAT gateway timeouts)
    "keepalives": 1,
    "keepalives_idle": 60,
    "keepalives_interval": 10,
    "keepalives_count": 5,

    # Server-side session timeouts passed as PostgreSQL GUC parameters
    "options": (
        f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS} "
        f"-c lock_timeout={settings.DB_LOCK_TIMEOUT_MS} "
        f"-c idle_in_transaction_session_timeout={settings.DB_IDLE_IN_TX_TIMEOUT_MS}"
    ),
}

engine = create_engine(
    _db_url,
    # Validate connections before checkout to avoid stale-connection errors
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    # Recycle connections before NAT/firewall idle timeouts can silently drop them
    pool_recycle=settings.DB_POOL_RECYCLE,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Pool monitoring event listeners

def _pool_status() -> dict:
    """Return a snapshot of current pool utilisation."""
    pool = engine.pool
    size: int = pool.size()
    checked_out: int = pool.checkedout()
    overflow: int = pool.overflow()
    active_overflow = max(0, overflow)
    total_capacity = size + settings.DB_MAX_OVERFLOW
    utilization = (checked_out + active_overflow) / total_capacity if total_capacity else 0
    return {
        "pool_size": size,
        "checked_out": checked_out,
        "overflow": overflow,
        "total_capacity": total_capacity,
        "utilization_pct": round(utilization * 100, 1),
    }


@event.listens_for(engine, "connect")
def _on_connect(dbapi_connection, connection_record) -> None:
    """Log each new physical connection established."""
    logger.info("New physical DB connection established", extra=_pool_status())


@event.listens_for(engine, "checkout")
def _on_checkout(dbapi_connection, connection_record, connection_proxy) -> None:
    """Warn when pool utilisation approaches exhaustion."""
    s = _pool_status()
    if s["utilization_pct"] >= 90:
        logger.warning("DB pool utilization critical — risk of pool exhaustion", extra=s)
    elif s["utilization_pct"] >= 75:
        logger.warning("DB pool utilization high", extra=s)


@event.listens_for(engine, "checkin")
def _on_checkin(dbapi_connection, connection_record) -> None:
    """Log connection return when utilisation is still high."""
    s = _pool_status()
    if s["utilization_pct"] >= 75:
        logger.info("DB connection returned to pool (still high utilization)", extra=s)


# Retry decorator

def db_retry(
    max_attempts: int = settings.DB_RETRY_MAX_ATTEMPTS,
    min_wait: float = settings.DB_RETRY_MIN_WAIT_S,
    max_wait: float = settings.DB_RETRY_MAX_WAIT_S,
):
    """
    Decorator that retries a DB operation on transient errors with exponential backoff.

    Only OperationalError and InterfaceError are retried (network / stale connection).
    After all attempts are exhausted the original exception is re-raised.

    Example::

        @db_retry()
        def get_user(db: Session, user_id: int) -> User:
            return db.get(User, user_id)
    """
    return retry(
        retry=retry_if_exception_type((OperationalError, InterfaceError)),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# FastAPI dependency

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Guarantees rollback on error and connection return to pool via finally.
    """
    db = SessionLocal()
    try:
        yield db
    except OperationalError as exc:
        db.rollback()
        logger.error(
            "SQLAlchemy OperationalError in request session",
            extra={"orig": str(getattr(exc, "orig", exc))},
            exc_info=True,
        )
        raise
    except InterfaceError as exc:
        db.rollback()
        logger.error(
            "SQLAlchemy InterfaceError in request session",
            extra={"orig": str(getattr(exc, "orig", exc))},
            exc_info=True,
        )
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
