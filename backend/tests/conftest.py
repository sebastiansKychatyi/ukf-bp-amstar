"""Shared pytest fixtures for the AmStar test suite."""

import pytest
import pytest_asyncio
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_captain

# Import all models so Base.metadata.create_all() registers every table
from app.db.base import (          # noqa: F401
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
    connect_args={"check_same_thread": False},  # required for SQLite shared across threads
    poolclass=StaticPool,  # single connection ensures create_all and test sessions share one DB
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# INFRASTRUCTURE FIXTURES

@pytest.fixture(autouse=True)
def disable_startup_events():
    """Prevent FastAPI startup events from connecting to PostgreSQL/Redis during tests."""
    saved_startup  = app.router.on_startup[:]
    saved_shutdown = app.router.on_shutdown[:]
    app.router.on_startup.clear()
    app.router.on_shutdown.clear()
    yield
    app.router.on_startup  = saved_startup
    app.router.on_shutdown = saved_shutdown


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    """Replace the Redis client with a mock so tests don't require a running Redis."""
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
    """Fresh SQLite session per test; tables are created before and dropped after."""
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
    """Captain who sends challenges (Team Alpha's owner)."""
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
    """Captain who receives challenges (Team Beta's owner)."""
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
    """Regular player without CAPTAIN role (used to test 403 responses)."""
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


# CHALLENGE FIXTURE

@pytest.fixture
def accepted_challenge(db: Session, team_a: Team, team_b: Team) -> Challenge:
    """Challenge already in ACCEPTED state, ready for result submission."""
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


# HTTP CLIENT FIXTURES

@pytest_asyncio.fixture
async def client_captain_a(db: Session, captain_a: User, team_a: Team) -> AsyncClient:
    """Async HTTP client authenticated as captain_a (no JWT validation)."""
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
    Async HTTP client authenticated as a regular player.

    get_current_captain is intentionally not overridden so the real role
    check runs and returns 403 for PLAYER-role users.
    """
    def override_db():
        yield db

    app.dependency_overrides[get_db]                  = override_db
    app.dependency_overrides[get_current_active_user] = lambda: player_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
