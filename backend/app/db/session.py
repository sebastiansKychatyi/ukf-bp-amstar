"""
Database Session Management — AmStar Platform

Hardened production configuration для синхронного SQLAlchemy 2.0 + psycopg2.

Ключевые защитные механизмы:
  1. pool_pre_ping     — проверяет живость соединения перед выдачей из пула
  2. pool_recycle      — пересоздаёт соединения раньше, чем NAT/FW убьёт их
  3. TCP keepalives    — обнаруживает «тихие» обрывы без ожидания kernel timeout
  4. Statement timeout — предотвращает блокировку пула долгими запросами
  5. Event listeners   — мониторинг утилизации пула в реальном времени
  6. db_retry()        — прозрачный retry с экспоненциальным backoff для transient-ошибок
"""

import logging
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Строка подключения
# ---------------------------------------------------------------------------
# Если DATABASE_URL задан через postgresql+psycopg2://, оставляем как есть.
# Если через postgresql://, psycopg2 подхватит его автоматически.
_db_url = settings.DATABASE_URL

# ---------------------------------------------------------------------------
# connect_args — параметры передаются напрямую в драйвер psycopg2
# ---------------------------------------------------------------------------
_connect_args = {
    # connect_timeout: сколько секунд ждать TCP handshake с сервером БД.
    # По умолчанию ядро ждёт ~120s — это неприемлемо в облаке, где недоступная
    # БД должна быть обнаружена быстро, а не висеть в pending-соединении.
    "connect_timeout": settings.DB_CONNECT_TIMEOUT,

    # TCP Keepalives — предотвращают «тихие» обрывы:
    # NAT-шлюзы (AWS NAT GW) и балансировщики (ALB, NLB) молча дропают
    # idle TCP-сессии через 60–350 секунд без уведомления обеих сторон.
    # Приложение при этом держит «соединение» в пуле, которое на самом деле
    # мертво — и обнаруживает это только при следующем запросе (= UnknownError).
    # Keepalives заставляют ядро периодически отправлять ACK-пробы:
    "keepalives": 1,           # включить TCP keepalives для этого соединения
    "keepalives_idle": 60,     # первый probe через 60s idle (< NAT timeout ≈ 60-350s)
    "keepalives_interval": 10, # повторять probe каждые 10s
    "keepalives_count": 5,     # 5 неудачных probe → соединение считается мёртвым

    # Серверные таймауты передаются через GUC-параметры сессии:
    # statement_timeout: если запрос выполняется дольше N мс — отменить.
    #   Без этого один «тяжёлый» запрос может заблокировать соединение из пула
    #   на неограниченное время, постепенно исчерпывая pool_size.
    # lock_timeout: защита от deadlock-ожидания (блокировки на уровне строк/таблиц).
    # idle_in_transaction_session_timeout: убивает сессии, открывшие транзакцию
    #   и «забывшие» её закрыть — частая причина «утечки» соединений из пула.
    "options": (
        f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS} "
        f"-c lock_timeout={settings.DB_LOCK_TIMEOUT_MS} "
        f"-c idle_in_transaction_session_timeout={settings.DB_IDLE_IN_TX_TIMEOUT_MS}"
    ),
}

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    _db_url,

    # pool_pre_ping: перед выдачей соединения из пула выполняет "SELECT 1".
    # Если соединение мертво (stale after NAT drop) — автоматически переустанавливает.
    # Это устраняет топ-1 причину "UnreachableDatabase / Unknown":
    # когда пул возвращает соединение, которое NAT-шлюз уже закрыл со своей стороны.
    pool_pre_ping=True,

    # pool_size: базовое число постоянных соединений.
    # Правило: pool_size ≈ (CPU-cores * 2) или (max_concurrent_requests * 0.8).
    # Для FastAPI под uvicorn с 4 workers — 20 достаточно.
    pool_size=settings.DB_POOL_SIZE,

    # max_overflow: дополнительные соединения сверх pool_size на время пика.
    # Итого лимит: pool_size + max_overflow = 30 (должно быть < max_connections PostgreSQL / 2).
    # Эти соединения закрываются сразу после использования, не возвращаясь в пул.
    max_overflow=settings.DB_MAX_OVERFLOW,

    # pool_timeout: сколько секунд ждать свободного слота в пуле.
    # Без этого при исчерпании пула запрос висит вечно.
    # После timeout бросается sqlalchemy.exc.TimeoutError — явная, классифицируемая ошибка.
    pool_timeout=settings.DB_POOL_TIMEOUT,

    # pool_recycle: принудительно пересоздавать соединения каждые N секунд.
    # AWS NAT Gateway убивает idle TCP через ~350s, некоторые FW через 60s.
    # 1800s (30 мин) гарантирует ротацию задолго до любого из этих порогов.
    pool_recycle=settings.DB_POOL_RECYCLE,

    connect_args=_connect_args,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    # expire_on_commit=True по умолчанию: атрибуты ORM-объектов сбрасываются
    # после commit(), что заставляет перечитывать из БД — безопаснее.
)


# ---------------------------------------------------------------------------
# Event listeners — мониторинг пула
# ---------------------------------------------------------------------------

def _pool_status() -> dict:
    """Снимок текущего состояния пула соединений."""
    pool = engine.pool
    size: int = pool.size()
    checked_out: int = pool.checkedout()
    overflow: int = pool.overflow()
    # overflow() может быть отрицательным (свободные overflow-слоты)
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
    """Логируем каждое новое физическое соединение с БД."""
    status = _pool_status()
    logger.info(
        "New physical DB connection established",
        extra=status,
    )


@event.listens_for(engine, "checkout")
def _on_checkout(dbapi_connection, connection_record, connection_proxy) -> None:
    """
    Срабатывает каждый раз, когда соединение выдаётся из пула.

    Логируем предупреждение, если утилизация пула превысила 90% — это
    ранний сигнал о надвигающемся pool exhaustion (TimeoutError).
    При 100% утилизации следующий запрос будет ждать pool_timeout секунд.
    """
    status = _pool_status()
    if status["utilization_pct"] >= 90:
        logger.warning(
            "DB pool utilization critical — risk of pool exhaustion",
            extra=status,
        )
    elif status["utilization_pct"] >= 75:
        logger.warning(
            "DB pool utilization high",
            extra=status,
        )


@event.listens_for(engine, "checkin")
def _on_checkin(dbapi_connection, connection_record) -> None:
    """
    Логируем возврат соединения в пул только если утилизация всё ещё высокая —
    помогает отследить момент, когда пик прошёл.
    """
    status = _pool_status()
    if status["utilization_pct"] >= 75:
        logger.info(
            "DB connection returned to pool (still high utilization)",
            extra=status,
        )


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------
# Ретраим ТОЛЬКО transient-ошибки:
#   OperationalError — сеть, stale-соединение, restart сервера
#   InterfaceError   — низкоуровневые ошибки драйвера при разрыве
#
# НЕ ретраим:
#   IntegrityError  — нарушение constraint (retry бессмысленен)
#   ProgrammingError — ошибка в SQL (retry бессмысленен)
#   TimeoutError    — pool exhaustion (retry только усугубит)
#   DataError       — плохие данные (retry бессмысленен)
#
# Почему именно эти wait-параметры:
#   min=0.5s: достаточно для TCP reconnect, не слишком долго для пользователя
#   max=10s: даём серверу время на restart, но не держим запрос вечно
#   multiplier=1: экспоненциальный рост: 0.5 → 1 → 2 → 4 → ... capped at 10

def db_retry(
    max_attempts: int = settings.DB_RETRY_MAX_ATTEMPTS,
    min_wait: float = settings.DB_RETRY_MIN_WAIT_S,
    max_wait: float = settings.DB_RETRY_MAX_WAIT_S,
):
    """
    Декоратор для операций с БД с экспоненциальным backoff.

    Использование — на уровне сервисной функции:

        @db_retry()
        def get_user_by_id(db: Session, user_id: int) -> User:
            return db.get(User, user_id)

    Если все попытки исчерпаны, tenacity перебрасывает оригинальный exception.
    """
    return retry(
        retry=retry_if_exception_type((OperationalError, InterfaceError)),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        # before_sleep_log логирует попытку и задержку перед следующим retry
        before_sleep=before_sleep_log(logger, logging.WARNING),
        # reraise=True: после исчерпания попыток бросает оригинальный exception,
        # а не tenacity.RetryError — это важно для корректной работы exception handlers
        reraise=True,
    )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency для инъекции DB-сессии в endpoint.

    Гарантирует:
      - rollback при любой необработанной ошибке внутри endpoint
      - закрытие соединения (возврат в пул) в блоке finally
      - логирование DB-ошибок с контекстом (тип ошибки, первопричина)
    """
    db = SessionLocal()
    try:
        yield db
    except OperationalError as exc:
        # Rollback перед закрытием — не оставляем транзакцию висеть
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
