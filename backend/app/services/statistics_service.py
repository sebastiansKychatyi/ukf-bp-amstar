"""
Player Statistics Service

Handles the two-tier statistics architecture:

1. **MatchPlayerStatistics** — per-match granular data (source of truth)
2. **PlayerStatistics** — aggregated lifetime totals (derived / cache)

After every match, per-player stats are recorded into MatchPlayerStatistics.
Then the aggregated PlayerStatistics row is recomputed by summing all
per-match records for that player.  This ensures data integrity:
the aggregated row can always be rebuilt from the transactional records.

Data-integrity rule
-------------------
A player can only have MatchPlayerStatistics for a challenge in which
their team actually participated.  The service enforces this at write time
by verifying that the player's team_id matches either the challenger_id
or the opponent_id of the challenge.
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.player_statistics import PlayerStatistics, MatchPlayerStatistics
from app.models.challenge import Challenge, ChallengeStatus
from app.models.team_member import TeamMember
from app.models.user import User
from app.models.team import Team
from app.schemas.player_statistics import (
    MatchPlayerStatisticsCreate,
    MatchPlayerStatisticsResponse,
    PlayerStatisticsResponse,
    PlayerProfileWithStats,
)
from app.services.base import BaseService
from app.core.exceptions import (
    ChallengeNotFoundError,
    UserNotFoundError,
    TeamNotFoundError,
    InsufficientPermissionsError,
    BusinessRuleViolationError,
)


class StatisticsService(BaseService[PlayerStatistics]):
    """
    Service for recording and aggregating player statistics.
    """

    def __init__(self, db: Session):
        super().__init__(db)

    # =====================================================================
    # MATCH STATISTICS (per-match recording)
    # =====================================================================

    def record_match_stats(
        self,
        challenge_id: int,
        stats_list: List[MatchPlayerStatisticsCreate],
    ) -> List[MatchPlayerStatisticsResponse]:
        """
        Record per-player statistics for a completed match.

        Validates:
        - Challenge exists and is COMPLETED
        - Each player's team actually participated in the challenge
        - No duplicate stats for the same player in the same challenge

        After recording, aggregated PlayerStatistics are rebuilt for
        every affected player.

        Args:
            challenge_id: ID of the completed challenge.
            stats_list: List of per-player stat entries.

        Returns:
            List of created MatchPlayerStatisticsResponse.
        """
        challenge = self.db.query(Challenge).filter(
            Challenge.id == challenge_id
        ).first()
        if not challenge:
            raise ChallengeNotFoundError(challenge_id)
        if challenge.status != ChallengeStatus.COMPLETED:
            raise BusinessRuleViolationError(
                message="Can only record stats for completed challenges",
                error_code="CHALLENGE_NOT_COMPLETED",
            )

        valid_team_ids = {challenge.challenger_id, challenge.opponent_id}
        created = []
        affected_user_ids = set()

        for entry in stats_list:
            # Integrity check: player's team must be in the match
            if entry.team_id not in valid_team_ids:
                raise BusinessRuleViolationError(
                    message=f"Team {entry.team_id} did not participate in challenge {challenge_id}",
                    error_code="TEAM_NOT_IN_CHALLENGE",
                )

            # No duplicate per-match entries
            existing = self.db.query(MatchPlayerStatistics).filter(
                MatchPlayerStatistics.challenge_id == challenge_id,
                MatchPlayerStatistics.user_id == entry.user_id,
            ).first()
            if existing:
                raise BusinessRuleViolationError(
                    message=f"Stats already recorded for player {entry.user_id} in challenge {challenge_id}",
                    error_code="DUPLICATE_MATCH_STATS",
                )

            row = MatchPlayerStatistics(
                user_id=entry.user_id,
                challenge_id=challenge_id,
                team_id=entry.team_id,
                goals=entry.goals,
                assists=entry.assists,
                yellow_cards=entry.yellow_cards,
                red_cards=entry.red_cards,
                minutes_played=entry.minutes_played,
                shots_on_target=entry.shots_on_target,
                saves=entry.saves,
            )
            self.db.add(row)
            created.append(row)
            affected_user_ids.add(entry.user_id)

        self.db.commit()
        for row in created:
            self.db.refresh(row)

        # Reaggregate for all affected players
        for user_id in affected_user_ids:
            self._reaggregate_player(user_id, challenge)

        self._log_operation(
            "Match stats recorded",
            challenge_id=challenge_id,
            player_count=len(created),
        )

        return [MatchPlayerStatisticsResponse.model_validate(r) for r in created]

    # =====================================================================
    # AGGREGATION ENGINE
    # =====================================================================

    def _reaggregate_player(self, user_id: int, challenge: Challenge) -> None:
        """
        Recompute PlayerStatistics from all MatchPlayerStatistics for a user.

        This is an idempotent operation — running it multiple times
        produces the same result, because it reads from the source-of-truth
        (per-match records) and overwrites the aggregate.
        """
        # SUM all per-match stats
        agg = (
            self.db.query(
                func.count(MatchPlayerStatistics.id).label("matches_played"),
                func.coalesce(func.sum(MatchPlayerStatistics.goals), 0).label("goals"),
                func.coalesce(func.sum(MatchPlayerStatistics.assists), 0).label("assists"),
                func.coalesce(func.sum(MatchPlayerStatistics.shots_on_target), 0).label("shots_on_target"),
                func.coalesce(func.sum(MatchPlayerStatistics.yellow_cards), 0).label("yellow_cards"),
                func.coalesce(func.sum(MatchPlayerStatistics.red_cards), 0).label("red_cards"),
                func.coalesce(func.sum(MatchPlayerStatistics.saves), 0).label("saves"),
            )
            .filter(MatchPlayerStatistics.user_id == user_id)
            .first()
        )

        # Count wins / draws / losses by joining with Challenge
        match_records = (
            self.db.query(MatchPlayerStatistics.team_id, Challenge)
            .join(Challenge, MatchPlayerStatistics.challenge_id == Challenge.id)
            .filter(
                MatchPlayerStatistics.user_id == user_id,
                Challenge.status == ChallengeStatus.COMPLETED,
            )
            .all()
        )

        wins = draws = losses = clean_sheets = 0
        for team_id, ch in match_records:
            if ch.challenger_score is None or ch.opponent_score is None:
                continue
            # Determine this player's team score vs opponent
            if ch.challenger_id == team_id:
                my_score, opp_score = ch.challenger_score, ch.opponent_score
            else:
                my_score, opp_score = ch.opponent_score, ch.challenger_score

            if my_score > opp_score:
                wins += 1
            elif my_score < opp_score:
                losses += 1
            else:
                draws += 1

            if opp_score == 0:
                clean_sheets += 1

        # Upsert the aggregate row
        stats = self.db.query(PlayerStatistics).filter(
            PlayerStatistics.user_id == user_id
        ).first()

        if not stats:
            stats = PlayerStatistics(user_id=user_id)
            self.db.add(stats)

        stats.matches_played = agg.matches_played or 0
        stats.matches_won = wins
        stats.matches_drawn = draws
        stats.matches_lost = losses
        stats.goals = agg.goals
        stats.assists = agg.assists
        stats.shots_on_target = agg.shots_on_target
        stats.yellow_cards = agg.yellow_cards
        stats.red_cards = agg.red_cards
        stats.saves = agg.saves
        stats.clean_sheets = clean_sheets

        self.db.commit()

    def rebuild_all_aggregates(self) -> int:
        """
        Full rebuild: reaggregate stats for every player who has
        at least one MatchPlayerStatistics record.

        Returns the number of players processed.
        """
        user_ids = [
            uid for (uid,) in
            self.db.query(MatchPlayerStatistics.user_id).distinct().all()
        ]
        for uid in user_ids:
            self._reaggregate_player(uid, None)
        self._log_operation("Full reaggregation", player_count=len(user_ids))
        return len(user_ids)

    # =====================================================================
    # QUERY METHODS
    # =====================================================================

    def get_player_stats(self, user_id: int) -> Optional[PlayerStatistics]:
        """Get aggregated statistics for a single player."""
        return self.db.query(PlayerStatistics).filter(
            PlayerStatistics.user_id == user_id
        ).first()

    def get_player_match_history(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[MatchPlayerStatistics]:
        """Get per-match stats for a player, newest first."""
        return (
            self.db.query(MatchPlayerStatistics)
            .filter(MatchPlayerStatistics.user_id == user_id)
            .order_by(MatchPlayerStatistics.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_top_scorers(self, limit: int = 20) -> list[dict]:
        """Leaderboard: players ranked by total goals."""
        rows = (
            self.db.query(PlayerStatistics)
            .join(User, PlayerStatistics.user_id == User.id)
            .order_by(PlayerStatistics.goals.desc())
            .limit(limit)
            .all()
        )
        return self._to_leaderboard(rows, "goals")

    def get_top_assists(self, limit: int = 20) -> list[dict]:
        """Leaderboard: players ranked by total assists."""
        rows = (
            self.db.query(PlayerStatistics)
            .join(User, PlayerStatistics.user_id == User.id)
            .order_by(PlayerStatistics.assists.desc())
            .limit(limit)
            .all()
        )
        return self._to_leaderboard(rows, "assists")

    def get_player_profile(self, user_id: int) -> PlayerProfileWithStats:
        """Full player profile with team info and aggregated stats."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(user_id)

        membership = self.db.query(TeamMember).filter(
            TeamMember.user_id == user_id
        ).first()

        team_name = None
        team_id = None
        position = None
        jersey_number = None
        if membership:
            team = self.db.query(Team).filter(Team.id == membership.team_id).first()
            team_name = team.name if team else None
            team_id = membership.team_id
            position = membership.position
            jersey_number = membership.jersey_number

        stats = self.get_player_stats(user_id)

        return PlayerProfileWithStats(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            team_name=team_name,
            team_id=team_id,
            position=position,
            jersey_number=jersey_number,
            statistics=PlayerStatisticsResponse.model_validate(stats) if stats else None,
        )

    # =====================================================================
    # HELPERS
    # =====================================================================

    def _to_leaderboard(self, rows: list, sort_field: str) -> list[dict]:
        """Convert PlayerStatistics rows to leaderboard dicts."""
        result = []
        for rank, stats in enumerate(rows, start=1):
            user = self.db.query(User).filter(User.id == stats.user_id).first()
            result.append({
                "rank": rank,
                "user_id": stats.user_id,
                "username": user.username if user else "Unknown",
                "full_name": user.full_name if user else None,
                sort_field: getattr(stats, sort_field),
                "matches_played": stats.matches_played,
            })
        return result
