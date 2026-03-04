"""
test_challenge_service.py — Unit tests for ChallengeService
=============================================================

These tests exercise the Battle System business logic directly at the
service layer, bypassing HTTP routing and authentication entirely.
Each test receives a real SQLAlchemy session connected to an in-memory
SQLite database, which makes the tests fast and fully isolated.

State machine under test:
    PENDING  →  ACCEPTED   (accept_challenge)
    PENDING  →  REJECTED   (reject_challenge)
    PENDING  →  CANCELLED  (cancel_challenge)
    ACCEPTED →  COMPLETED  (submit_result)
    ACCEPTED →  CANCELLED  (cancel_challenge)
    COMPLETED / REJECTED / CANCELLED  →  (terminal — no transitions allowed)
"""

import pytest
from sqlalchemy.orm import Session

from app.services.challenge_service import ChallengeService
from app.models.challenge import Challenge, ChallengeStatus
from app.models.team import Team
from app.models.user import User
from app.core.exceptions import (
    SelfChallengeError,
    InvalidChallengeStatusError,
    NotTeamOwnerError,
    TeamNotFoundError,
    InsufficientPermissionsError,
)


# =============================================================================
# HELPER
# =============================================================================

def make_service(db: Session) -> ChallengeService:
    return ChallengeService(db)


# =============================================================================
# TC-S01  Creating a new challenge
# =============================================================================

class TestCreateChallenge:

    def test_create_challenge_success(
        self, db: Session, captain_a: User, team_a: Team, team_b: Team
    ):
        """
        TC-S01-A: A captain can create a challenge targeting a different team.

        Verifies:
        - The returned challenge has status PENDING.
        - challenger_id and opponent_id are correctly set.
        - The challenge is persisted in the database.
        """
        svc = make_service(db)

        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
            location="Štadión Nitra",
        )

        assert challenge.id is not None
        assert challenge.status == ChallengeStatus.PENDING
        assert challenge.challenger_id == team_a.id
        assert challenge.opponent_id  == team_b.id
        assert challenge.location == "Štadión Nitra"

        # Verify persistence
        db_record = db.query(Challenge).filter(Challenge.id == challenge.id).first()
        assert db_record is not None

    def test_create_challenge_self_challenge_raises(
        self, db: Session, captain_a: User, team_a: Team
    ):
        """
        TC-S01-B: A captain cannot challenge their own team.

        Verifies that SelfChallengeError is raised when opponent_id
        equals the captain's own team id.
        """
        svc = make_service(db)

        with pytest.raises(SelfChallengeError):
            svc.create_challenge(
                challenger_captain_id=captain_a.id,
                opponent_id=team_a.id,       # same team → self-challenge
            )

    def test_create_challenge_nonexistent_opponent_raises(
        self, db: Session, captain_a: User, team_a: Team
    ):
        """
        TC-S01-C: Challenge to a non-existent team raises TeamNotFoundError.

        Verifies that the service validates the opponent's existence before
        creating the challenge record.
        """
        svc = make_service(db)

        with pytest.raises(TeamNotFoundError):
            svc.create_challenge(
                challenger_captain_id=captain_a.id,
                opponent_id=99999,           # does not exist
            )

    def test_create_challenge_duplicate_pending_raises(
        self, db: Session, captain_a: User, team_a: Team, team_b: Team
    ):
        """
        TC-S01-D: A duplicate PENDING challenge between the same two teams
        is rejected by the system.

        Verifies that the service enforces the no-duplicate-pending rule,
        preventing the same matchup from being queued twice.
        """
        svc = make_service(db)

        # First challenge — should succeed
        svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )

        # Second challenge — same pair, still PENDING → must fail
        with pytest.raises(InvalidChallengeStatusError):
            svc.create_challenge(
                challenger_captain_id=captain_a.id,
                opponent_id=team_b.id,
            )


# =============================================================================
# TC-S02  Accepting a challenge
# =============================================================================

class TestAcceptChallenge:

    def test_accept_challenge_transitions_to_accepted(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S02-A: Opponent captain can accept a PENDING challenge.

        Verifies the state machine transition PENDING → ACCEPTED and that
        the updated status is persisted.
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )

        accepted = svc.accept_challenge(challenge.id, captain_b.id)

        assert accepted.status == ChallengeStatus.ACCEPTED

    def test_accept_challenge_wrong_captain_raises(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S02-B: The *challenger's* captain cannot accept their own challenge.

        Verifies that the service correctly enforces the ownership rule:
        only the captain of the *opponent* team may accept.
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )

        with pytest.raises(NotTeamOwnerError):
            svc.accept_challenge(challenge.id, captain_a.id)  # wrong side

    def test_accept_already_accepted_challenge_raises(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S02-C: Accepting an already ACCEPTED challenge raises
        InvalidChallengeStatusError.

        Verifies that duplicate accept calls are rejected by the state machine.
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )
        svc.accept_challenge(challenge.id, captain_b.id)  # first accept

        with pytest.raises(InvalidChallengeStatusError):
            svc.accept_challenge(challenge.id, captain_b.id)  # second accept


# =============================================================================
# TC-S03  Rejecting a challenge
# =============================================================================

class TestRejectChallenge:

    def test_reject_challenge_transitions_to_rejected(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S03-A: Opponent captain can reject a PENDING challenge.

        Verifies the state machine transition PENDING → REJECTED and that
        REJECTED is a terminal state (no further transitions possible).
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )

        rejected = svc.reject_challenge(challenge.id, captain_b.id)

        assert rejected.status == ChallengeStatus.REJECTED

    def test_cannot_accept_rejected_challenge(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S03-B: A REJECTED challenge cannot be accepted (terminal state).

        Verifies that REJECTED is a dead-end in the state machine.
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )
        svc.reject_challenge(challenge.id, captain_b.id)

        with pytest.raises(InvalidChallengeStatusError):
            svc.accept_challenge(challenge.id, captain_b.id)


# =============================================================================
# TC-S04  Cancelling a challenge
# =============================================================================

class TestCancelChallenge:

    def test_cancel_pending_challenge(
        self,
        db: Session,
        captain_a: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S04-A: Challenger captain can cancel a PENDING challenge.

        Verifies the state machine transition PENDING → CANCELLED.
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )

        cancelled = svc.cancel_challenge(challenge.id, captain_a.id)

        assert cancelled.status == ChallengeStatus.CANCELLED

    def test_cancel_accepted_challenge(
        self,
        db: Session,
        captain_a: User,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S04-B: Challenger captain can cancel an ACCEPTED challenge.

        Verifies the state machine transition ACCEPTED → CANCELLED,
        which is permitted to handle last-minute withdrawals.
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )
        svc.accept_challenge(challenge.id, captain_b.id)

        cancelled = svc.cancel_challenge(challenge.id, captain_a.id)

        assert cancelled.status == ChallengeStatus.CANCELLED

    def test_cancel_completed_challenge_raises(
        self,
        db: Session,
        accepted_challenge: Challenge,
        captain_a: User,
        team_a: Team,
    ):
        """
        TC-S04-C: A COMPLETED challenge cannot be cancelled (terminal state).

        Verifies that once a match result is recorded, the challenge is
        immutable and no further state transitions are possible.
        """
        svc = make_service(db)
        # Manually set to COMPLETED to simulate a finished match
        accepted_challenge.status = ChallengeStatus.COMPLETED
        accepted_challenge.challenger_score = 2
        accepted_challenge.opponent_score   = 1
        db.commit()

        with pytest.raises(InvalidChallengeStatusError):
            svc.cancel_challenge(accepted_challenge.id, captain_a.id)


# =============================================================================
# TC-S05  Submitting a match result
# =============================================================================

class TestSubmitResult:

    def test_submit_result_transitions_to_completed(
        self,
        db: Session,
        accepted_challenge: Challenge,
        captain_a: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S05-A: Either participating captain can submit the match result.

        Verifies the state machine transition ACCEPTED → COMPLETED and
        that the scores are persisted on the challenge record.
        """
        svc = make_service(db)

        completed = svc.submit_result(
            challenge_id=accepted_challenge.id,
            user_id=captain_a.id,
            challenger_score=3,
            opponent_score=1,
        )

        assert completed.status           == ChallengeStatus.COMPLETED
        assert completed.challenger_score == 3
        assert completed.opponent_score   == 1

    def test_submit_result_by_opponent_captain(
        self,
        db: Session,
        accepted_challenge: Challenge,
        captain_b: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S05-B: The *opponent* captain can also submit the result.

        Verifies that permission is granted to both participating captains,
        not just the one who created the challenge.
        """
        svc = make_service(db)

        completed = svc.submit_result(
            challenge_id=accepted_challenge.id,
            user_id=captain_b.id,        # opponent side
            challenger_score=0,
            opponent_score=2,
        )

        assert completed.status == ChallengeStatus.COMPLETED

    def test_submit_result_from_non_participant_raises(
        self,
        db: Session,
        accepted_challenge: Challenge,
        player_user: User,
    ):
        """
        TC-S05-C: A user not part of either team cannot submit the result.

        Verifies that InsufficientPermissionsError is raised for third parties,
        preventing fraudulent result submissions.
        """
        svc = make_service(db)

        with pytest.raises(InsufficientPermissionsError):
            svc.submit_result(
                challenge_id=accepted_challenge.id,
                user_id=player_user.id,  # not a captain of either team
                challenger_score=1,
                opponent_score=1,
            )

    def test_submit_result_on_pending_challenge_raises(
        self,
        db: Session,
        captain_a: User,
        team_a: Team,
        team_b: Team,
    ):
        """
        TC-S05-D: Cannot submit a result for a PENDING challenge.

        Verifies that result submission is only possible from ACCEPTED state,
        enforcing the correct lifecycle order (accept first, play, then score).
        """
        svc = make_service(db)
        challenge = svc.create_challenge(
            challenger_captain_id=captain_a.id,
            opponent_id=team_b.id,
        )
        # challenge is still PENDING — not yet accepted

        with pytest.raises(InvalidChallengeStatusError):
            svc.submit_result(
                challenge_id=challenge.id,
                user_id=captain_a.id,
                challenger_score=2,
                opponent_score=0,
            )
