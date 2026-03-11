"""
ELO Rating Service

Implements the Elo rating system adapted for team sports.

The Elo system, originally devised by Arpad Elo for chess (1960),
provides a method for calculating the relative skill levels of
competitors.  This implementation adapts the standard formulas
for two-team football matches.

Core formulas
-------------

1. **Expected score** of team A against team B:

       E_A = 1 / (1 + 10^((R_B - R_A) / 400))

   where R_A and R_B are the current ratings.

2. **Actual score** S_A:

       S_A = 1.0  (win)
       S_A = 0.5  (draw)
       S_A = 0.0  (loss)

3. **Rating update**:

       R'_A = R_A + K * (S_A - E_A)

   where K is a dynamic factor that controls rating volatility.

K-factor policy
---------------

The K-factor varies by team maturity to let newcomers converge
faster while keeping established teams stable:

    Matches played < 10  → K = 40  (provisional)
    Matches played < 30  → K = 30  (developing)
    Matches played >= 30 → K = 20  (established)

Additionally, a goal-difference multiplier amplifies K for
decisive victories, rewarding dominant performance:

    G = 1 + ln(1 + |goal_diff|)

    Effective K = base_K * G
"""

import math
from typing import Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.team import Team
from app.models.challenge import Challenge, ChallengeStatus
from app.models.rating import Rating
from app.schemas.challenge import EloUpdateResult
from app.services.base import BaseService
from app.services.team_category import get_team_category
from app.core.exceptions import TeamNotFoundError, ChallengeNotFoundError


class EloService(BaseService[Rating]):
    """
    Service for computing and persisting ELO rating updates.
    """

    def __init__(self, db: Session):
        super().__init__(db)

    # =====================================================================
    # PUBLIC API
    # =====================================================================

    def update_ratings(
        self,
        challenge_id: int,
    ) -> Tuple[EloUpdateResult, EloUpdateResult]:
        """
        Compute and persist ELO rating changes after a completed challenge.

        This is the main entry point — called by the challenge endpoint
        immediately after transitioning a challenge to COMPLETED.

        Args:
            challenge_id: ID of the completed challenge.

        Returns:
            Tuple of (challenger_update, opponent_update).

        Raises:
            ChallengeNotFoundError: If challenge doesn't exist.
            ValueError: If challenge is not in COMPLETED state or has no scores.
        """
        challenge = (
            self.db.query(Challenge)
            .filter(Challenge.id == challenge_id)
            .first()
        )
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)

        if challenge.status != ChallengeStatus.COMPLETED:
            raise ValueError(
                f"Cannot compute ELO for challenge in state '{challenge.status.value}'"
            )
        if challenge.challenger_score is None or challenge.opponent_score is None:
            raise ValueError("Challenge has no recorded scores")

        # Load both teams
        team_a = self.db.query(Team).filter(Team.id == challenge.challenger_id).first()
        team_b = self.db.query(Team).filter(Team.id == challenge.opponent_id).first()
        if not team_a or not team_b:
            raise TeamNotFoundError(
                challenge.challenger_id if not team_a else challenge.opponent_id
            )

        r_a = team_a.rating or 1000
        r_b = team_b.rating or 1000

        # Determine actual scores
        s_a, s_b = self._actual_scores(
            challenge.challenger_score, challenge.opponent_score
        )
        goal_diff = abs(challenge.challenger_score - challenge.opponent_score)

        # Count past matches for K-factor determination
        matches_a = self._count_completed_matches(team_a.id)
        matches_b = self._count_completed_matches(team_b.id)

        # Compute K-factors
        k_a = self._dynamic_k_factor(matches_a, goal_diff)
        k_b = self._dynamic_k_factor(matches_b, goal_diff)

        # Expected scores
        e_a = self._expected_score(r_a, r_b)
        e_b = 1.0 - e_a  # by definition E_A + E_B = 1

        # New ratings
        new_r_a = round(r_a + k_a * (s_a - e_a))
        new_r_b = round(r_b + k_b * (s_b - e_b))

        # Floor at 0
        new_r_a = max(0, new_r_a)
        new_r_b = max(0, new_r_b)

        # Persist rating changes
        self._save_rating_record(team_a.id, challenge_id, r_a, new_r_a)
        self._save_rating_record(team_b.id, challenge_id, r_b, new_r_b)

        team_a.rating = new_r_a
        team_b.rating = new_r_b
        self.db.commit()

        self._log_operation(
            "ELO updated",
            challenge_id=challenge_id,
            team_a=f"{team_a.name}: {r_a}→{new_r_a}",
            team_b=f"{team_b.name}: {r_b}→{new_r_b}",
        )

        return (
            EloUpdateResult(
                team_id=team_a.id,
                team_name=team_a.name,
                old_rating=r_a,
                new_rating=new_r_a,
                rating_change=new_r_a - r_a,
            ),
            EloUpdateResult(
                team_id=team_b.id,
                team_name=team_b.name,
                old_rating=r_b,
                new_rating=new_r_b,
                rating_change=new_r_b - r_b,
            ),
        )

    def get_leaderboard(
        self, skip: int = 0, limit: int = 50
    ) -> list[dict]:
        """
        Return teams ranked by ELO rating (descending).
        """
        teams = (
            self.db.query(Team)
            .order_by(Team.rating.desc().nullslast())
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []
        for rank, team in enumerate(teams, start=skip + 1):
            matches = self._count_completed_matches(team.id)
            result.append({
                "rank": rank,
                "team_id": team.id,
                "team_name": team.name,
                "city": team.city,
                "rating": team.rating or 1000,
                "matches_played": matches,
            })
        return result

    def get_rating_history(self, team_id: int) -> list[dict]:
        """
        Return the chronological rating history for a team.

        Useful for rendering a rating-progression chart on the frontend.
        """
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)

        records = (
            self.db.query(Rating)
            .filter(Rating.team_id == team_id)
            .order_by(Rating.created_at.asc())
            .all()
        )
        return [
            {
                "challenge_id": r.challenge_id,
                "old_rating": r.old_rating,
                "new_rating": r.new_rating,
                "rating_change": r.rating_change,
                "date": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]

    # =====================================================================
    # CORE MATHEMATICAL FUNCTIONS
    # =====================================================================

    @staticmethod
    def _expected_score(r_a: int, r_b: int) -> float:
        """
        Compute the expected score of team A vs team B.

            E_A = 1 / (1 + 10^((R_B - R_A) / 400))
        """
        return 1.0 / (1.0 + math.pow(10, (r_b - r_a) / 400.0))

    @staticmethod
    def _actual_scores(score_a: int, score_b: int) -> Tuple[float, float]:
        """
        Map a match result to ELO actual-score pairs.

            Win  → (1.0, 0.0)
            Draw → (0.5, 0.5)
            Loss → (0.0, 1.0)
        """
        if score_a > score_b:
            return 1.0, 0.0
        elif score_a < score_b:
            return 0.0, 1.0
        else:
            return 0.5, 0.5

    @staticmethod
    def _goal_difference_multiplier(goal_diff: int) -> float:
        """
        Amplify K-factor based on goal difference.

            G = 1 + ln(1 + |goal_diff|)

        This rewards dominant victories without being excessively punitive.
        A 1-goal win gives G ≈ 1.69; a 5-goal win gives G ≈ 2.79.
        """
        return 1.0 + math.log(1.0 + goal_diff)

    def _dynamic_k_factor(self, matches_played: int, goal_diff: int) -> float:
        """
        Select the base K-factor by team maturity, then scale by goal difference.

            K_eff = K_base * G(|goal_diff|)
        """
        base_k = get_team_category(matches_played).k_factor
        return base_k * self._goal_difference_multiplier(goal_diff)

    # =====================================================================
    # DATA HELPERS
    # =====================================================================

    def _count_completed_matches(self, team_id: int) -> int:
        """Count completed challenges for a team (used for K-factor tier)."""
        return (
            self.db.query(func.count(Challenge.id))
            .filter(
                Challenge.status == ChallengeStatus.COMPLETED,
                or_(
                    Challenge.challenger_id == team_id,
                    Challenge.opponent_id == team_id,
                ),
            )
            .scalar()
        ) or 0

    def _save_rating_record(
        self,
        team_id: int,
        challenge_id: int,
        old_rating: int,
        new_rating: int,
    ) -> None:
        """Persist a Rating history row."""
        record = Rating(
            team_id=team_id,
            challenge_id=challenge_id,
            old_rating=old_rating,
            new_rating=new_rating,
            rating_change=new_rating - old_rating,
        )
        self.db.add(record)
