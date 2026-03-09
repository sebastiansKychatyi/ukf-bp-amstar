"""
Challenge Service — State Machine & Business Logic

Implements the complete lifecycle of a team-vs-team challenge:

    ┌─────────┐   accept    ┌──────────┐  submit_result  ┌───────────┐
    │ PENDING │────────────►│ ACCEPTED │────────────────►│ COMPLETED │
    └────┬────┘             └─────┬────┘                 └───────────┘
         │                        │
         │  reject                │  cancel
         ▼                        ▼
    ┌──────────┐            ┌───────────┐
    │ REJECTED │            │ CANCELLED │
    └──────────┘            └───────────┘

Valid state transitions:
    PENDING  → ACCEPTED | REJECTED | CANCELLED
    ACCEPTED → COMPLETED | CANCELLED
    REJECTED → (terminal)
    COMPLETED → (terminal)
    CANCELLED → (terminal)
"""

from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from app.models.team import Team
from app.models.challenge import Challenge, ChallengeStatus
from app.models.team_member import TeamMember
from app.models.notification import NotificationType
from app.services.base import BaseService
from app.services.notification_service import NotificationService
from app.core.exceptions import (
    ChallengeNotFoundError,
    TeamNotFoundError,
    SelfChallengeError,
    InvalidChallengeStatusError,
    NotTeamOwnerError,
    InsufficientPermissionsError,
)


# Allowed state transitions (state machine)
_VALID_TRANSITIONS = {
    ChallengeStatus.PENDING: {
        ChallengeStatus.ACCEPTED,
        ChallengeStatus.REJECTED,
        ChallengeStatus.CANCELLED,
    },
    ChallengeStatus.ACCEPTED: {
        ChallengeStatus.COMPLETED,
        ChallengeStatus.CANCELLED,
    },
    # Terminal states — no outgoing transitions
    ChallengeStatus.REJECTED: set(),
    ChallengeStatus.COMPLETED: set(),
    ChallengeStatus.CANCELLED: set(),
}


class ChallengeService(BaseService[Challenge]):
    """
    Service class implementing the Challenge state machine.

    Every public method enforces:
    1. Entity existence checks
    2. Ownership / permission validation
    3. State-transition legality
    """

    def __init__(self, db: Session):
        super().__init__(db)
        self._notifier = NotificationService(db)

    # =====================================================================
    # RETRIEVAL
    # =====================================================================

    def get_challenge(self, challenge_id: int) -> Challenge:
        """Get a single challenge with team relationships eagerly loaded."""
        challenge = (
            self.db.query(Challenge)
            .options(
                joinedload(Challenge.challenger),
                joinedload(Challenge.opponent),
            )
            .filter(Challenge.id == challenge_id)
            .first()
        )
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)
        return challenge

    def get_challenges(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ChallengeStatus] = None,
        team_id: Optional[int] = None,
    ) -> tuple[List[Challenge], int]:
        """
        List challenges with optional filters.

        Returns (items, total_count) for pagination.
        """
        # Base filter query (no joinedload — avoids COUNT over JOIN giving inflated totals)
        filter_query = self.db.query(Challenge)

        if status:
            filter_query = filter_query.filter(Challenge.status == status)
        if team_id:
            filter_query = filter_query.filter(
                or_(
                    Challenge.challenger_id == team_id,
                    Challenge.opponent_id == team_id,
                )
            )

        total = filter_query.count()

        # Separate fetch query with eager loading
        items = (
            filter_query
            .options(
                joinedload(Challenge.challenger),
                joinedload(Challenge.opponent),
            )
            .order_by(Challenge.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def get_team_challenges(
        self,
        team_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Challenge], int]:
        """Get all challenges involving a specific team."""
        return self.get_challenges(skip=skip, limit=limit, team_id=team_id)

    # =====================================================================
    # STATE TRANSITIONS
    # =====================================================================

    def create_challenge(
        self,
        challenger_captain_id: int,
        opponent_id: int,
        match_date: Optional[datetime] = None,
        location: Optional[str] = None,
    ) -> Challenge:
        """
        Captain A creates a challenge targeting Team B.

        Validations:
        - Captain must own a team
        - Cannot challenge own team
        - Opponent team must exist
        - No duplicate pending challenge between same teams
        """
        # Find challenger's team
        challenger_team = (
            self.db.query(Team)
            .filter(Team.captain_id == challenger_captain_id)
            .first()
        )
        if not challenger_team:
            raise TeamNotFoundError(f"captain_{challenger_captain_id}")

        # Cannot self-challenge
        if challenger_team.id == opponent_id:
            raise SelfChallengeError()

        # Opponent must exist
        opponent_team = self.db.query(Team).filter(Team.id == opponent_id).first()
        if not opponent_team:
            raise TeamNotFoundError(opponent_id)

        # No duplicate pending challenges between same pair
        existing = (
            self.db.query(Challenge)
            .filter(
                Challenge.status == ChallengeStatus.PENDING,
                or_(
                    (Challenge.challenger_id == challenger_team.id)
                    & (Challenge.opponent_id == opponent_id),
                    (Challenge.challenger_id == opponent_id)
                    & (Challenge.opponent_id == challenger_team.id),
                ),
            )
            .first()
        )
        if existing:
            raise InvalidChallengeStatusError(
                "pending", "pending — a challenge between these teams already exists"
            )

        challenge = Challenge(
            challenger_id=challenger_team.id,
            opponent_id=opponent_id,
            status=ChallengeStatus.PENDING,
            match_date=match_date,
            location=location,
        )
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)

        # Notify opponent captain
        self._notifier.notify(
            user_id=opponent_team.captain_id,
            type=NotificationType.CHALLENGE_RECEIVED,
            title="New Challenge",
            message=f"{challenger_team.name} challenged your team!",
            related_id=challenge.id,
        )
        self.db.commit()

        self._log_operation(
            "Challenge created",
            challenge_id=challenge.id,
            challenger=challenger_team.name,
            opponent=opponent_team.name,
        )
        return self.get_challenge(challenge.id)

    def accept_challenge(
        self, challenge_id: int, captain_id: int
    ) -> Challenge:
        """
        Opponent captain accepts the challenge.

        Only the captain of the *opponent* team may accept.
        Transition: PENDING → ACCEPTED
        """
        challenge = self.get_challenge(challenge_id)
        self._assert_opponent_captain(challenge, captain_id)
        self._transition(challenge, ChallengeStatus.ACCEPTED)

        self._notifier.notify(
            user_id=challenge.challenger.captain_id,
            type=NotificationType.CHALLENGE_ACCEPTED,
            title="Challenge Accepted",
            message=f"{challenge.opponent.name} accepted your challenge!",
            related_id=challenge.id,
        )
        self.db.commit()

        return self.get_challenge(challenge_id)

    def reject_challenge(
        self, challenge_id: int, captain_id: int
    ) -> Challenge:
        """
        Opponent captain rejects the challenge.

        Transition: PENDING → REJECTED
        """
        challenge = self.get_challenge(challenge_id)
        self._assert_opponent_captain(challenge, captain_id)
        self._transition(challenge, ChallengeStatus.REJECTED)

        self._notifier.notify(
            user_id=challenge.challenger.captain_id,
            type=NotificationType.CHALLENGE_REJECTED,
            title="Challenge Rejected",
            message=f"{challenge.opponent.name} rejected your challenge.",
            related_id=challenge.id,
        )
        self.db.commit()

        return self.get_challenge(challenge_id)

    def cancel_challenge(
        self, challenge_id: int, captain_id: int
    ) -> Challenge:
        """
        Challenger captain cancels the challenge.

        Allowed from PENDING or ACCEPTED states.
        Transition: PENDING|ACCEPTED → CANCELLED
        """
        challenge = self.get_challenge(challenge_id)
        self._assert_challenger_captain(challenge, captain_id)
        self._transition(challenge, ChallengeStatus.CANCELLED)
        return self.get_challenge(challenge_id)

    def submit_result(
        self,
        challenge_id: int,
        user_id: int,
        challenger_score: int,
        opponent_score: int,
    ) -> Challenge:
        """
        Record match result and transition to COMPLETED.

        Either captain of the participating teams or a referee can submit.
        Transition: ACCEPTED → COMPLETED

        After completion, the ELO update is handled externally by the
        caller (endpoint) which invokes EloService.update_ratings().
        """
        challenge = self.get_challenge(challenge_id)

        # Permission: must be captain of either team or referee
        is_challenger_captain = challenge.challenger.captain_id == user_id
        is_opponent_captain = challenge.opponent.captain_id == user_id
        if not (is_challenger_captain or is_opponent_captain):
            raise InsufficientPermissionsError(
                "Only a captain of one of the participating teams can submit the result"
            )

        self._transition(challenge, ChallengeStatus.COMPLETED)
        challenge.challenger_score = challenger_score
        challenge.opponent_score = opponent_score
        self.db.commit()
        self.db.refresh(challenge)

        # Notify both captains
        score_text = f"{challenger_score}-{opponent_score}"
        for cap_id, team_name in [
            (challenge.challenger.captain_id, challenge.opponent.name),
            (challenge.opponent.captain_id, challenge.challenger.name),
        ]:
            self._notifier.notify(
                user_id=cap_id,
                type=NotificationType.CHALLENGE_COMPLETED,
                title="Match Completed",
                message=f"Result vs {team_name}: {score_text}",
                related_id=challenge.id,
            )
        self.db.commit()

        self._log_operation(
            "Match result submitted",
            challenge_id=challenge_id,
            score=score_text,
        )
        return self.get_challenge(challenge_id)

    # =====================================================================
    # INTERNAL HELPERS
    # =====================================================================

    def _transition(self, challenge: Challenge, target: ChallengeStatus) -> None:
        """
        Execute a state transition with validation.

        Raises InvalidChallengeStatusError if the transition is not allowed
        by the state machine definition.
        """
        allowed = _VALID_TRANSITIONS.get(challenge.status, set())
        if target not in allowed:
            raise InvalidChallengeStatusError(
                challenge.status.value, target.value
            )

        challenge.status = target
        challenge.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        self._log_operation(
            "Challenge state transition",
            challenge_id=challenge.id,
            transition=f"{challenge.status.value} → {target.value}",
        )

    def _assert_opponent_captain(
        self, challenge: Challenge, user_id: int
    ) -> None:
        """Verify that user_id is the captain of the opponent team."""
        opponent = self.db.query(Team).filter(
            Team.id == challenge.opponent_id
        ).first()
        if not opponent or opponent.captain_id != user_id:
            raise NotTeamOwnerError()

    def _assert_challenger_captain(
        self, challenge: Challenge, user_id: int
    ) -> None:
        """Verify that user_id is the captain of the challenger team."""
        challenger = self.db.query(Team).filter(
            Team.id == challenge.challenger_id
        ).first()
        if not challenger or challenger.captain_id != user_id:
            raise NotTeamOwnerError()
