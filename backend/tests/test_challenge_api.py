"""
test_challenge_api.py — HTTP integration tests for /api/v1/challenges
=======================================================================

These tests send real HTTP requests through the FastAPI ASGI app using
httpx.AsyncClient with ASGITransport (no TCP connection to a real server).

The auth dependencies (get_current_active_user, get_current_captain) are
replaced via app.dependency_overrides, so no JWT tokens are needed.

The database dependency (get_db) is replaced with a test SQLite session
from conftest.py, so no PostgreSQL connection is required.

Covered endpoints:
    POST   /api/v1/challenges/              create_challenge
    GET    /api/v1/challenges/{id}          get_challenge
    PUT    /api/v1/challenges/{id}/accept   accept_challenge
    PUT    /api/v1/challenges/{id}/reject   reject_challenge
    PUT    /api/v1/challenges/{id}/cancel   cancel_challenge
    PUT    /api/v1/challenges/{id}/result   submit_result
    GET    /api/v1/challenges/              list_challenges
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.challenge import Challenge, ChallengeStatus
from app.models.team import Team
from app.models.user import User

BASE = "/api/v1/challenges"


# =============================================================================
# TC-A01  POST /challenges/  — create a challenge
# =============================================================================

class TestCreateChallengeEndpoint:

    async def test_create_challenge_returns_201(
        self,
        client_captain_a: AsyncClient,
        team_b: Team,
    ):
        """
        TC-A01-A: Valid POST by a captain returns HTTP 201 Created.

        The response body must include id, status='pending', challenger_id,
        and opponent_id matching the payload.
        """
        payload = {"opponent_id": team_b.id, "location": "Štadión Nitra"}

        response = await client_captain_a.post(f"{BASE}/", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["status"]      == "pending"
        assert body["opponent_id"] == team_b.id
        assert "id" in body

    async def test_create_challenge_player_role_forbidden(
        self,
        client_player: AsyncClient,
        team_b: Team,
    ):
        """
        TC-A01-B: A user without CAPTAIN role receives HTTP 403 Forbidden.

        Verifies that the RoleChecker dependency correctly denies access
        to non-captain users attempting to create challenges.
        """
        payload = {"opponent_id": team_b.id}

        response = await client_player.post(f"{BASE}/", json=payload)

        assert response.status_code == 403

    async def test_create_challenge_missing_opponent_id_returns_422(
        self,
        client_captain_a: AsyncClient,
    ):
        """
        TC-A01-C: Missing required field opponent_id returns HTTP 422.

        Verifies Pydantic schema validation at the API boundary.
        """
        response = await client_captain_a.post(f"{BASE}/", json={})

        assert response.status_code == 422

    async def test_create_challenge_self_challenge_returns_400(
        self,
        client_captain_a: AsyncClient,
        team_a: Team,
    ):
        """
        TC-A01-D: Challenging own team returns HTTP 400 Bad Request.

        The endpoint maps SelfChallengeError → 400 via the _handle() helper.
        """
        payload = {"opponent_id": team_a.id}   # own team

        response = await client_captain_a.post(f"{BASE}/", json=payload)

        assert response.status_code == 400


# =============================================================================
# TC-A02  GET /challenges/{id}  — retrieve a challenge
# =============================================================================

class TestGetChallengeEndpoint:

    async def test_get_existing_challenge_returns_200(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A02-A: GET on an existing challenge returns HTTP 200 with
        the full challenge object.
        """
        # Seed a challenge directly in the DB
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        db.add(challenge)
        db.commit()

        response = await client_captain_a.get(f"{BASE}/{challenge.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"]     == challenge.id
        assert body["status"] == "pending"

    async def test_get_nonexistent_challenge_returns_404(
        self,
        client_captain_a: AsyncClient,
    ):
        """
        TC-A02-B: GET on a non-existent challenge ID returns HTTP 404.

        Verifies that ChallengeNotFoundError is correctly mapped to 404.
        """
        response = await client_captain_a.get(f"{BASE}/99999")

        assert response.status_code == 404


# =============================================================================
# TC-A03  PUT /challenges/{id}/accept
# =============================================================================

class TestAcceptChallengeEndpoint:

    async def test_accept_challenge_returns_200_and_accepted_status(
        self,
        client_captain_b: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A03-A: Opponent captain accepts a PENDING challenge.

        Verifies that the endpoint returns HTTP 200 and the response
        body contains status='accepted'.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        db.add(challenge)
        db.commit()

        response = await client_captain_b.put(f"{BASE}/{challenge.id}/accept")

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    async def test_accept_challenge_wrong_captain_returns_403(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A03-B: The challenger's captain cannot accept their own challenge.

        Verifies the 403 response when NotTeamOwnerError is raised by the
        service layer.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        db.add(challenge)
        db.commit()

        # captain_a is the *challenger* — not allowed to accept
        response = await client_captain_a.put(f"{BASE}/{challenge.id}/accept")

        assert response.status_code == 403


# =============================================================================
# TC-A04  PUT /challenges/{id}/reject
# =============================================================================

class TestRejectChallengeEndpoint:

    async def test_reject_challenge_returns_200_and_rejected_status(
        self,
        client_captain_b: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A04-A: Opponent captain rejects a PENDING challenge.

        Verifies HTTP 200 and status='rejected' in the response body.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        db.add(challenge)
        db.commit()

        response = await client_captain_b.put(f"{BASE}/{challenge.id}/reject")

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"


# =============================================================================
# TC-A05  PUT /challenges/{id}/cancel
# =============================================================================

class TestCancelChallengeEndpoint:

    async def test_cancel_pending_challenge_returns_200(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A05-A: Challenger captain cancels a PENDING challenge.

        Verifies HTTP 200 and status='cancelled'.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        db.add(challenge)
        db.commit()

        response = await client_captain_a.put(f"{BASE}/{challenge.id}/cancel")

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    async def test_cancel_completed_challenge_returns_409(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A05-B: Cancelling a COMPLETED challenge returns HTTP 409 Conflict.

        Verifies that terminal states are enforced at the HTTP layer.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.COMPLETED,
            challenger_score=2,
            opponent_score=1,
        )
        db.add(challenge)
        db.commit()

        response = await client_captain_a.put(f"{BASE}/{challenge.id}/cancel")

        assert response.status_code == 409


# =============================================================================
# TC-A06  PUT /challenges/{id}/result  — submit result & trigger ELO
# =============================================================================

class TestSubmitResultEndpoint:

    async def test_submit_result_returns_200_with_elo_updates(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A06-A: Submitting a valid result transitions the challenge to
        COMPLETED and returns ELO update data for both teams.

        This is the most critical end-to-end test of the Battle System:
        it validates the full pipeline from HTTP request through service
        layer to ELO calculation and database persistence.

        Expected response structure:
            {
                "challenge": { "status": "completed", ... },
                "elo_updates": [
                    { "team_id": ..., "old_rating": 1000, "new_rating": ..., ... },
                    { "team_id": ..., "old_rating": 1000, "new_rating": ..., ... },
                ]
            }
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.ACCEPTED,
        )
        db.add(challenge)
        db.commit()

        payload = {"challenger_score": 3, "opponent_score": 1}
        response = await client_captain_a.put(
            f"{BASE}/{challenge.id}/result", json=payload
        )

        assert response.status_code == 200
        body = response.json()

        # Challenge status
        assert body["challenge"]["status"] == "completed"
        assert body["challenge"]["challenger_score"] == 3
        assert body["challenge"]["opponent_score"]   == 1

        # ELO updates
        elo_updates = body["elo_updates"]
        assert len(elo_updates) == 2

        team_ids_in_response = {u["team_id"] for u in elo_updates}
        assert team_a.id in team_ids_in_response
        assert team_b.id in team_ids_in_response

        # Winner gains, loser loses
        winner_update = next(u for u in elo_updates if u["team_id"] == team_a.id)
        loser_update  = next(u for u in elo_updates if u["team_id"] == team_b.id)
        assert winner_update["rating_change"] > 0
        assert loser_update["rating_change"]  < 0

    async def test_submit_result_on_pending_challenge_returns_409(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A06-B: Submitting a result for a PENDING challenge (not yet
        accepted) returns HTTP 409 Conflict.

        Verifies the lifecycle order: a challenge must be ACCEPTED before
        a result can be recorded.
        """
        challenge = Challenge(
            challenger_id=team_a.id,
            opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,   # not yet accepted
        )
        db.add(challenge)
        db.commit()

        payload = {"challenger_score": 2, "opponent_score": 0}
        response = await client_captain_a.put(
            f"{BASE}/{challenge.id}/result", json=payload
        )

        assert response.status_code == 409


# =============================================================================
# TC-A07  GET /challenges/  — list with filters
# =============================================================================

class TestListChallengesEndpoint:

    async def test_list_challenges_returns_paginated_response(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A07-A: GET /challenges/ returns a paginated response object.

        Verifies the response schema: { items: [...], total: int,
        skip: int, limit: int }.
        """
        # Seed two challenges
        for _ in range(2):
            challenge = Challenge(
                challenger_id=team_a.id,
                opponent_id=team_b.id,
                status=ChallengeStatus.PENDING,
            )
            db.add(challenge)
        db.commit()

        response = await client_captain_a.get(f"{BASE}/")

        assert response.status_code == 200
        body = response.json()
        assert "items"  in body
        assert "total"  in body
        assert "skip"   in body
        assert "limit"  in body
        assert body["total"] >= 2

    async def test_list_challenges_filter_by_status(
        self,
        client_captain_a: AsyncClient,
        db: Session,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-A07-B: The ?status= query parameter filters results correctly.

        Seeds one PENDING and one ACCEPTED challenge, then verifies that
        filtering by status=accepted returns only the accepted challenge.
        """
        pending_ch = Challenge(
            challenger_id=team_a.id, opponent_id=team_b.id,
            status=ChallengeStatus.PENDING,
        )
        accepted_ch = Challenge(
            challenger_id=team_b.id, opponent_id=team_a.id,
            status=ChallengeStatus.ACCEPTED,
        )
        db.add_all([pending_ch, accepted_ch])
        db.commit()

        response = await client_captain_a.get(f"{BASE}/?status=accepted")

        assert response.status_code == 200
        body = response.json()
        for item in body["items"]:
            assert item["status"] == "accepted"
