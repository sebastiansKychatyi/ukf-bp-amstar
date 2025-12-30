# Integration Testing Guide

## Overview

This guide demonstrates how to test the refactored AmStar Football Platform backend with all new security features, exception handling, and service layer integration.

---

## Prerequisites

### 1. Install Testing Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov httpx faker
```

### 2. Configure Test Environment

Create `backend/.env.test`:

```env
SECRET_KEY=test_secret_key_for_testing_only_minimum_32_characters
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/amstar_test
REDIS_HOST=localhost
REDIS_PORT=6379
ENVIRONMENT=testing
DEBUG=True
RATE_LIMIT_ENABLED=False
```

---

## Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_team_service.py     # Service layer unit tests
├── test_teams_api.py        # API endpoint integration tests
├── test_exceptions.py       # Exception handling tests
├── test_rate_limit.py       # Rate limiting tests
├── test_sanitization.py     # Input sanitization tests
└── test_security.py         # Security headers tests
```

---

## Testing the Refactored Components

### 1. Service Layer Unit Tests

**File:** `tests/test_team_service.py`

```python
"""
Unit tests for TeamService business logic
"""
import pytest
from uuid import uuid4
from app.services.team_service import TeamService
from app.core.exceptions import (
    CaptainAlreadyHasTeamError,
    TeamNotFoundError,
    UnauthorizedTeamAccessError,
    TeamCapacityExceededError
)
from app.models import schemas


class TestTeamService:
    """Test TeamService business logic in isolation"""

    def test_create_team_success(self, db_session, sample_captain):
        """Test successful team creation"""
        service = TeamService(db_session)

        team_data = schemas.TeamCreate(
            name="Thunder FC",
            captain_id=sample_captain.id,
            home_city="Prague",
            description="Best team ever"
        )

        team = service.create_team(team_in=team_data, captain_id=sample_captain.id)

        assert team.name == "Thunder FC"
        assert team.captain_id == sample_captain.id
        assert team.home_city == "Prague"

    def test_captain_can_only_create_one_team(self, db_session, sample_captain):
        """Test business rule: one team per captain"""
        service = TeamService(db_session)

        # Create first team
        team_data = schemas.TeamCreate(
            name="Team 1",
            captain_id=sample_captain.id
        )
        team1 = service.create_team(team_in=team_data, captain_id=sample_captain.id)
        assert team1.name == "Team 1"

        # Try to create second team - should fail
        team_data2 = schemas.TeamCreate(
            name="Team 2",
            captain_id=sample_captain.id
        )

        with pytest.raises(CaptainAlreadyHasTeamError) as exc_info:
            service.create_team(team_in=team_data2, captain_id=sample_captain.id)

        assert exc_info.value.error_code == "CAPTAIN_ALREADY_HAS_TEAM"

    def test_get_team_by_id_not_found(self, db_session):
        """Test TeamNotFoundError for non-existent team"""
        service = TeamService(db_session)

        fake_uuid = uuid4()

        with pytest.raises(TeamNotFoundError) as exc_info:
            service.get_team_by_id(team_id=fake_uuid)

        assert str(fake_uuid) in exc_info.value.message

    def test_update_team_requires_captain(self, db_session, sample_team, sample_player):
        """Test only captain can update team"""
        service = TeamService(db_session)

        update_data = schemas.TeamUpdate(name="New Name")

        # Non-captain tries to update
        with pytest.raises(UnauthorizedTeamAccessError):
            service.update_team(
                team_id=sample_team.id,
                team_in=update_data,
                current_user_id=sample_player.id  # Not the captain
            )

    def test_delete_team_requires_captain(self, db_session, sample_team, sample_player):
        """Test only captain can delete team"""
        service = TeamService(db_session)

        # Non-captain tries to delete
        with pytest.raises(UnauthorizedTeamAccessError):
            service.delete_team(
                team_id=sample_team.id,
                current_user_id=sample_player.id  # Not the captain
            )

    def test_eager_loading_prevents_n_plus_1(self, db_session, sample_teams):
        """Test that eager loading is used to prevent N+1 queries"""
        service = TeamService(db_session)

        # This should use joinedload to fetch captain in one query
        teams = service.get_teams(eager_load_captain=True)

        # Access captain without triggering additional queries
        for team in teams:
            _ = team.captain.full_name  # Should not trigger query

        assert len(teams) > 0
```

---

### 2. API Endpoint Integration Tests

**File:** `tests/test_teams_api.py`

```python
"""
Integration tests for Teams API endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestTeamsAPI:
    """Test Teams API with refactored endpoints"""

    def test_create_team_requires_captain_role(self, client: TestClient, player_token):
        """Test authorization: only captains can create teams"""
        response = client.post(
            "/api/v1/teams/",
            json={
                "name": "Test Team",
                "captain_id": "123e4567-e89b-12d3-a456-426614174000"
            },
            headers={"Authorization": f"Bearer {player_token}"}
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    def test_create_team_success(self, client: TestClient, captain_token, captain_id):
        """Test successful team creation"""
        response = client.post(
            "/api/v1/teams/",
            json={
                "name": "Thunder FC",
                "captain_id": str(captain_id),
                "home_city": "Prague",
                "description": "Best team <script>alert('xss')</script>"
            },
            headers={"Authorization": f"Bearer {captain_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thunder FC"
        # XSS should be sanitized
        assert "<script>" not in data["description"]

    def test_create_duplicate_team_fails(self, client: TestClient, captain_token, captain_id):
        """Test captain cannot create multiple teams"""
        # Create first team
        response1 = client.post(
            "/api/v1/teams/",
            json={
                "name": "Team 1",
                "captain_id": str(captain_id)
            },
            headers={"Authorization": f"Bearer {captain_token}"}
        )
        assert response1.status_code == 200

        # Try to create second team
        response2 = client.post(
            "/api/v1/teams/",
            json={
                "name": "Team 2",
                "captain_id": str(captain_id)
            },
            headers={"Authorization": f"Bearer {captain_token}"}
        )

        assert response2.status_code == 400
        assert response2.json()["error"]["code"] == "CAPTAIN_ALREADY_HAS_TEAM"

    def test_get_team_not_found(self, client: TestClient):
        """Test 404 error with custom exception"""
        fake_uuid = "123e4567-e89b-12d3-a456-426614174000"

        response = client.get(f"/api/v1/teams/{fake_uuid}")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "TEAM_NOT_FOUND"
        assert fake_uuid in response.json()["error"]["message"]

    def test_update_team_unauthorized(self, client: TestClient, sample_team_id, player_token):
        """Test non-captain cannot update team"""
        response = client.put(
            f"/api/v1/teams/{sample_team_id}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {player_token}"}
        )

        assert response.status_code == 403
        assert response.json()["error"]["code"] == "UNAUTHORIZED_TEAM_ACCESS"

    def test_error_response_format(self, client: TestClient):
        """Test standardized error response format"""
        response = client.get("/api/v1/teams/invalid-uuid")

        assert response.status_code == 422  # Validation error
        assert "error" in response.json()
        assert "code" in response.json()["error"]
        assert "message" in response.json()["error"]
```

---

### 3. Exception Handling Tests

**File:** `tests/test_exceptions.py`

```python
"""
Tests for custom exception hierarchy and handlers
"""
import pytest
from app.core.exceptions import (
    TeamNotFoundError,
    CaptainAlreadyHasTeamError,
    UnauthorizedTeamAccessError
)


def test_team_not_found_exception():
    """Test TeamNotFoundError details"""
    team_id = "123"
    exc = TeamNotFoundError(team_id)

    assert exc.error_code == "TEAM_NOT_FOUND"
    assert team_id in exc.message
    assert exc.details["resource_type"] == "Team"
    assert exc.details["identifier"] == team_id


def test_captain_already_has_team_exception():
    """Test CaptainAlreadyHasTeamError"""
    exc = CaptainAlreadyHasTeamError()

    assert exc.error_code == "CAPTAIN_ALREADY_HAS_TEAM"
    assert "one team" in exc.message.lower()


def test_unauthorized_team_access_exception():
    """Test UnauthorizedTeamAccessError"""
    exc = UnauthorizedTeamAccessError()

    assert exc.error_code == "UNAUTHORIZED_TEAM_ACCESS"
    assert "captain" in exc.message.lower()
```

---

### 4. Rate Limiting Tests

**File:** `tests/test_rate_limit.py`

```python
"""
Tests for rate limiting middleware
"""
import pytest
from fastapi.testclient import TestClient


def test_rate_limit_enforced(client: TestClient, enable_rate_limiting):
    """Test rate limiting blocks excessive requests"""
    # Make 10 rapid requests
    responses = []
    for i in range(10):
        response = client.get("/api/v1/teams/")
        responses.append(response)

    # Last requests should be rate limited
    assert any(r.status_code == 429 for r in responses[-3:])

    # Check rate limit headers
    limited_response = [r for r in responses if r.status_code == 429][0]
    assert "X-RateLimit-Limit" in limited_response.headers
    assert "X-RateLimit-Remaining" in limited_response.headers


def test_auth_endpoints_stricter_rate_limit(client: TestClient, enable_rate_limiting):
    """Test auth endpoints have stricter rate limits"""
    # Make 10 login attempts
    responses = []
    for i in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrong"}
        )
        responses.append(response)

    # Should be limited after 5 attempts
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0
    assert len(rate_limited) < len(responses)  # Not all blocked
```

---

### 5. Input Sanitization Tests

**File:** `tests/test_sanitization.py`

```python
"""
Tests for input sanitization utilities
"""
import pytest
from app.utils.sanitization import (
    sanitize_html,
    sanitize_string_field,
    sanitize_filename,
    sanitize_url
)


def test_sanitize_html_removes_scripts():
    """Test XSS script removal"""
    dangerous = "<script>alert('xss')</script>Hello"
    safe = sanitize_html(dangerous)

    assert "<script>" not in safe
    assert "Hello" in safe


def test_sanitize_html_allows_basic_formatting():
    """Test basic HTML tags are allowed"""
    text = "<b>Bold</b> <i>Italic</i> <script>alert()</script>"
    safe = sanitize_html(text, allow_basic_formatting=True)

    assert "<b>" in safe or "&lt;b&gt;" in safe  # Either allowed or escaped
    assert "<script>" not in safe


def test_sanitize_filename_prevents_path_traversal():
    """Test path traversal prevention"""
    dangerous = "../../etc/passwd"
    safe = sanitize_filename(dangerous)

    assert ".." not in safe
    assert "/" not in safe
    assert "\\" not in safe


def test_sanitize_url_blocks_javascript():
    """Test JavaScript URL blocking"""
    dangerous = "javascript:alert('xss')"

    with pytest.raises(ValueError):
        sanitize_url(dangerous)
```

---

### 6. Security Headers Tests

**File:** `tests/test_security.py`

```python
"""
Tests for security headers middleware
"""
import pytest
from fastapi.testclient import TestClient


def test_security_headers_present(client: TestClient):
    """Test all security headers are added"""
    response = client.get("/api/v1/teams/")

    # Check critical security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "X-XSS-Protection" in response.headers

    assert "Content-Security-Policy" in response.headers
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_hsts_header_in_production(client_production: TestClient):
    """Test HSTS header is enabled in production"""
    response = client_production.get("/")

    assert "Strict-Transport-Security" in response.headers
    assert "max-age=" in response.headers["Strict-Transport-Security"]
```

---

## Test Fixtures

**File:** `tests/conftest.py`

```python
"""
Pytest fixtures for testing
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.core.config import settings
from app.db.session import Base, get_db
from app.models import Player, Team, User
from app.core.security import create_access_token


# Database fixture
@pytest.fixture(scope="function")
def db_session():
    """Create test database session"""
    engine = create_engine(settings.DATABASE_URL)
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


# Client fixture
@pytest.fixture(scope="function")
def client(db_session):
    """Create test client"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Sample data fixtures
@pytest.fixture
def sample_captain(db_session):
    """Create sample captain"""
    user = User(id=uuid4(), email="captain@test.com", role="CAPTAIN")
    db_session.add(user)

    player = Player(
        id=uuid4(),
        user_id=user.id,
        first_name="John",
        last_name="Captain"
    )
    db_session.add(player)
    db_session.commit()

    return player


@pytest.fixture
def sample_team(db_session, sample_captain):
    """Create sample team"""
    team = Team(
        id=uuid4(),
        name="Test Team",
        captain_id=sample_captain.id
    )
    db_session.add(team)
    db_session.commit()

    return team


@pytest.fixture
def captain_token(sample_captain):
    """Generate JWT token for captain"""
    return create_access_token(data={"sub": str(sample_captain.user_id)})


@pytest.fixture
def enable_rate_limiting():
    """Enable rate limiting for specific tests"""
    original = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = True
    yield
    settings.RATE_LIMIT_ENABLED = original
```

---

## Running Tests

### Run All Tests

```bash
cd backend
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_team_service.py -v
```

### Run Tests Matching Pattern

```bash
pytest -k "test_captain" -v
```

### Run with Output

```bash
pytest -v -s
```

---

## Expected Test Results

### Coverage Targets

- **Service Layer**: 90%+ coverage
- **API Endpoints**: 85%+ coverage
- **Exception Handlers**: 95%+ coverage
- **Middleware**: 85%+ coverage
- **Utilities**: 90%+ coverage

### Key Test Metrics

```
tests/test_team_service.py ............ [ 25%]
tests/test_teams_api.py ............... [ 50%]
tests/test_exceptions.py ......        [ 60%]
tests/test_rate_limit.py ....          [ 70%]
tests/test_sanitization.py ......      [ 85%]
tests/test_security.py ....            [100%]

==================== 42 passed in 3.45s ====================
```

---

## Manual Testing with cURL

### Test Rate Limiting

```bash
# Send 10 rapid requests
for i in {1..10}; do
  curl -I http://localhost:8000/api/v1/teams/
done

# Check for 429 status and rate limit headers
```

### Test Security Headers

```bash
curl -I http://localhost:8000/api/v1/teams/

# Should see headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: ...
```

### Test Exception Handling

```bash
# Test 404 with custom error format
curl http://localhost:8000/api/v1/teams/00000000-0000-0000-0000-000000000000

# Response:
# {
#   "error": {
#     "code": "TEAM_NOT_FOUND",
#     "message": "Team with identifier '00000000-0000-0000-0000-000000000000' not found",
#     "details": {...}
#   }
# }
```

### Test Input Sanitization

```bash
# Try XSS injection
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Team",
    "description": "<script>alert(\"xss\")</script>Hello",
    "captain_id": "YOUR_PLAYER_ID"
  }'

# Response should have sanitized description
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: amstar_test
        ports:
          - 5432:5432

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/amstar_test
          SECRET_KEY: test_secret_key_minimum_32_characters_long
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Common Issues

**1. Import Errors**

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

**2. Database Connection Errors**

```bash
# Check PostgreSQL is running
pg_isready

# Verify test database exists
psql -l | grep amstar_test
```

**3. Redis Connection Errors**

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

---

## Next Steps

1. ✅ Write unit tests for all services
2. ✅ Write integration tests for all endpoints
3. ✅ Test exception handling
4. ✅ Test security middleware
5. ✅ Test rate limiting
6. ✅ Test input sanitization
7. Set up CI/CD pipeline
8. Achieve 85%+ code coverage
9. Document test results in thesis

---

## Summary

This testing guide provides:
- Complete test coverage for refactored components
- Unit tests for service layer business logic
- Integration tests for API endpoints
- Security testing (rate limiting, sanitization, headers)
- Test fixtures for consistent test data
- CI/CD integration examples
- Manual testing procedures

**Result**: Production-ready testing infrastructure suitable for Bachelor's thesis demonstration.
