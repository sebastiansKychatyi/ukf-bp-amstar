"""
conftest.py — Shared fixtures for the AmStar test suite
=========================================================

Database strategy: in-memory SQLite with StaticPool
-----------------------------------------------------
Every test function receives a *fresh* database session backed by an
in-memory SQLite instance.

IMPORTANT — why StaticPool is required
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
``sqlite:///:memory:`` creates a **per-connection** in-memory database.
SQLAlchemy's default QueuePool manages a pool of several connections.
``Base.metadata.create_all(bind=engine)`` creates tables on connection C1
and returns it to the pool.  If FastAPI's request handler later checks out
a *different* connection C2, that connection sees a brand-new, empty
in-memory database → ``OperationalError: no such table``.

``StaticPool`` fixes this by making the engine reuse a single connection
for every call.  ``create_all``, the test session, and the session injected
into FastAPI via ``override_get_db`` all operate on the **same** connection
and therefore the **same** in-memory database.

Authentication strategy: dependency override
---------------------------------------------
FastAPI's dependency-injection system is used to replace the real
JWT/Redis auth chain with simple callables that return pre-built
User objects.  This removes the need for a running Redis instance,
valid JWT tokens, or a production database during testing.

Startup event strategy: clear on entry, restore on exit
---------------------------------------------------------
The FastAPI startup event (create_all + redis.connect) is disabled
for the duration of the test session to prevent connection attempts
to infrastructure that is not available in CI.
"""

import pytest
import pytest_asyncio
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool          # ← required for in-memory SQLite
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_captain

# ── Import ALL models so that Base.metadata.create_all() sees every table ────
# This mirrors what app/db/base.py does for the production app.
from app.db.base import (          # noqa: F401  (side-effect import)
    Base,
    User, Team, Challenge, Rating,
    TeamMember, JoinRequest,
    PlayerStatistics, MatchPlayerStatistics,
    TeamAvailability, Notification,
    PasswordResetToken,
    Tournament, TournamentParticipant, TournamentMatch,
)
from app.models.user import UserRole
from app.models.challenge import ChallengeStatus


# ENGINE & SESSION FACTORY

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    # SQLite requires this flag when the same connection is shared
    # across different threads (e.g., FastAPI route handlers run in
    # a thread pool by Starlette's async-to-sync bridge).
    connect_args={"check_same_thread": False},
    # StaticPool forces every engine.connect() call to reuse the same
    # underlying connection object.  This is the standard solution for
    # in-memory SQLite tests: create_all() and all sessions share one
    # connection → one database → tables created once are always visible.
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# INFRASTRUCTURE FIXTURES

@pytest.fixture(autouse=True)
def disable_startup_events():
    """
    Clear FastAPI startup/shutdown handlers for every test.

    Without this, entering the httpx.AsyncClient context would trigger
    app.on_event("startup"), which tries to connect to the real
    PostgreSQL database and Redis.  We restore the handlers after each
    test so that the app object is not permanently mutated.
    """
    saved_startup  = app.router.on_startup[:]
    saved_shutdown = app.router.on_shutdown[:]
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    yield
    app.router.on_startup  = saved_startup
    app.router.on_shutdown = saved_shutdown


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """
    Replace the Redis client with a MagicMock for every test.

    The real redis_client is imported inside app.api.deps and
    app.core.redis; both references must be patched so that the
    is_token_blacklisted() call in get_current_user() never
    reaches a real Redis server.
    """
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.is_token_blacklisted.return_value = False
    mock.connect.return_value    = None
    mock.disconnect.return_value = None
    monkeypatch.setattr("app.api.deps.redis_client",  mock)
    monkeypatch.setattr("app.core.redis.redis_client", mock)


# DATABASE SESSION FIXTURE

@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Provide a clean SQLite session for a single test.

    - Creates all tables before the test body runs.
    - Yields the session so the test can seed data and call services.
    - Drops all tables after the test, regardless of pass/fail.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# USER FIXTURES

@pytest.fixture
def captain_a(db: Session) -> User:
    """The captain who will send challenges (Team Alpha's owner)."""
    user = User(
        email="captain_a@amstar.test",
        username="captain_alpha",
        hashed_password="$2b$12$test_hash_not_real",
        role=UserRole.CAPTAIN,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def captain_b(db: Session) -> User:
    """The captain who will receive challenges (Team Beta's owner)."""
    user = User(
        email="captain_b@amstar.test",
        username="captain_beta",
        hashed_password="$2b$12$test_hash_not_real",
        role=UserRole.CAPTAIN,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def player_user(db: Session) -> User:
    """A regular player without CAPTAIN role (used to test access denial)."""
    user = User(
        email="player@amstar.test",
        username="regular_player",
        hashed_password="$2b$12$test_hash_not_real",
        role=UserRole.PLAYER,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# TEAM FIXTURES

@pytest.fixture
def team_a(db: Session, captain_a: User) -> Team:
    """Team Alpha — owned by captain_a, starting ELO 1000."""
    team = Team(
        name="Team Alpha",
        captain_id=captain_a.id,
        rating=1000,
        city="Nitra",
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@pytest.fixture
def team_b(db: Session, captain_b: User) -> Team:
    """Team Beta — owned by captain_b, starting ELO 1000."""
    team = Team(
        name="Team Beta",
        captain_id=captain_b.id,
        rating=1000,
        city="Bratislava",
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


# CHALLENGE FIXTURE  (accepted, ready for result submission)

@pytest.fixture
def accepted_challenge(db: Session, team_a: Team, team_b: Team) -> Challenge:
    """
    A challenge that is already in ACCEPTED state.

    Used by tests that focus on result submission and ELO updates,
    skipping the creation/acceptance phase.
    """
    challenge = Challenge(
        challenger_id=team_a.id,
        opponent_id=team_b.id,
        status=ChallengeStatus.ACCEPTED,
        location="Štadión Nitra",
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


# HTTP CLIENT FIXTURES  (for API integration tests)

@pytest_asyncio.fixture
async def client_captain_a(db: Session, captain_a: User, team_a: Team) -> AsyncClient:
    """
    Async HTTP client authenticated as captain_a.

    - Routes all requests through the FastAPI ASGI app (no real TCP).
    - Overrides get_db to use the test SQLite session.
    - Overrides get_current_active_user and get_current_captain
      to return captain_a without any JWT validation.
    """
    def override_db():
        yield db

    app.dependency_overrides[get_db]                    = override_db
    app.dependency_overrides[get_current_active_user]   = lambda: captain_a
    app.dependency_overrides[get_current_captain]       = lambda: captain_a

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_captain_b(db: Session, captain_b: User, team_b: Team) -> AsyncClient:
    """Async HTTP client authenticated as captain_b (opponent side)."""
    def override_db():
        yield db

    app.dependency_overrides[get_db]                    = override_db
    app.dependency_overrides[get_current_active_user]   = lambda: captain_b
    app.dependency_overrides[get_current_captain]       = lambda: captain_b

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_player(db: Session, player_user: User) -> AsyncClient:
    """
    Async HTTP client authenticated as a regular player (no team).

    NOTE: get_current_captain is intentionally NOT overridden here.
    The real get_current_captain dependency must run so that it can
    inspect player_user.role, find it is not CAPTAIN, and raise 403.
    Overriding it would bypass the role check and expose service-layer
    errors (e.g. TeamNotFoundError → 404) instead of the expected 403.
    """
    def override_db():
        yield db

    app.dependency_overrides[get_db]                  = override_db
    app.dependency_overrides[get_current_active_user] = lambda: player_user
    # get_current_captain is deliberately left unoverridden so the
    # real role check executes and returns 403 for PLAYER-role users.

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
