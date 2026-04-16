import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Tuple

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_

from app.models.team import Team
from app.models.team_availability import TeamAvailability
from app.models.challenge import Challenge, ChallengeStatus
from app.models.team_member import TeamMember
from app.schemas.matchmaking import (
    MatchmakingSuggestion,
    MatchmakingScoreBreakdown,
    MatchmakingResponse,
    MatchmakingConfig,
    AvailabilitySlotCreate,
    AvailabilitySlotResponse,
    TeamAvailabilityResponse,
)
from app.services.base import BaseService
from app.core.exceptions import TeamNotFoundError


# Constants

# Earth radius in kilometres (used for Haversine formula)
_EARTH_RADIUS_KM = 6_371.0

# Maximum meaningful geographic distance (km).  Beyond this, geo score = 0.
_MAX_GEO_DISTANCE_KM = 100.0

# Recency window — matches within this period count towards the penalty.
_RECENCY_WINDOW_DAYS = 60

# Activity window — matches within this period count towards the bonus.
_ACTIVITY_WINDOW_DAYS = 90


class MatchmakingService(BaseService[Team]):
    """
    Service that implements the Smart Matchmaking Algorithm.

    The algorithm evaluates every eligible opponent team and produces
    a ranked list of suggestions ordered by the composite score S(T, O).
    """

    def __init__(self, db: Session):
        super().__init__(db)

    # Public methods

    def find_opponents(
        self,
        team_id: int,
        config: Optional[MatchmakingConfig] = None,
    ) -> MatchmakingResponse:
        """
        Main entry point: find and rank the best opponents for *team_id*.

        Steps:
        1. Load requesting team with availability.
        2. Fetch candidate opponents (excluding self, same-city preference).
        3. Pre-compute shared data (recent matches, activity counts).
        4. Score every candidate with the multi-factor formula.
        5. Sort descending and return top-N results.

        Args:
            team_id: ID of the team seeking an opponent.
            config:  Optional weight / parameter overrides.

        Returns:
            MatchmakingResponse with ranked suggestions.
        """
        cfg = config or MatchmakingConfig()

        # 1. Load requesting team
        team = (
            self.db.query(Team)
            .options(
                joinedload(Team.availability_slots),
                joinedload(Team.members),
            )
            .filter(Team.id == team_id)
            .first()
        )
        if not team:
            raise TeamNotFoundError(team_id)

        # 2. Fetch candidates (all other teams)
        candidates: List[Team] = (
            self.db.query(Team)
            .options(
                joinedload(Team.availability_slots),
                joinedload(Team.members),
            )
            .filter(Team.id != team_id)
            .all()
        )

        if not candidates:
            return MatchmakingResponse(
                requesting_team_id=team_id,
                requesting_team_rating=team.rating or 1000,
                suggestions=[],
                total_candidates=0,
            )

        # 3. Pre-compute batch data
        recent_opponents = self._get_recent_opponents(team_id)
        activity_map = self._get_activity_counts(
            [c.id for c in candidates]
        )

        # 4. Score each candidate
        scored: List[Tuple[float, MatchmakingSuggestion]] = []

        for candidate in candidates:
            elo_score = self._elo_similarity(team, candidate, cfg.elo_range)
            geo_score = self._geo_proximity(team, candidate)
            avail_score, overlap_count = self._availability_overlap(team, candidate)
            recency_score = self._recency_penalty(candidate.id, recent_opponents)
            activity_score = self._activity_bonus(candidate.id, activity_map)

            total = (
                cfg.w_elo * elo_score
                + cfg.w_geo * geo_score
                + cfg.w_avail * avail_score
                - cfg.w_recency * recency_score
                + cfg.w_activity * activity_score
            )
            # Clamp and scale to 0-100
            total = max(0.0, min(1.0, total)) * 100

            # Compute actual Haversine distance when both teams have coordinates
            distance_km: Optional[float] = None
            if (
                team.latitude is not None
                and team.longitude is not None
                and candidate.latitude is not None
                and candidate.longitude is not None
            ):
                distance_km = round(
                    _haversine(
                        team.latitude, team.longitude,
                        candidate.latitude, candidate.longitude,
                    ),
                    1,
                )

            suggestion = MatchmakingSuggestion(
                team_id=candidate.id,
                team_name=candidate.name,
                city=candidate.city,
                rating=candidate.rating or 1000,
                rating_difference=abs((team.rating or 1000) - (candidate.rating or 1000)),
                member_count=candidate.member_count,
                total_score=round(total, 2),
                breakdown=MatchmakingScoreBreakdown(
                    elo_similarity=round(elo_score, 4),
                    geo_proximity=round(geo_score, 4),
                    availability_overlap=round(avail_score, 4),
                    recency_penalty=round(recency_score, 4),
                    activity_bonus=round(activity_score, 4),
                ),
                overlapping_slots=overlap_count,
                distance_km=distance_km,
            )
            scored.append((total, suggestion))

        # 5. Sort and truncate
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [s for _, s in scored[: cfg.max_results]]

        self._log_operation(
            "Matchmaking completed",
            team_id=team_id,
            candidates_evaluated=len(candidates),
            suggestions_returned=len(top),
        )

        return MatchmakingResponse(
            requesting_team_id=team_id,
            requesting_team_rating=team.rating or 1000,
            suggestions=top,
            total_candidates=len(candidates),
        )

    # Availability management

    def get_team_availability(self, team_id: int) -> TeamAvailabilityResponse:
        """Return all availability slots for a team."""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)

        slots = (
            self.db.query(TeamAvailability)
            .filter(TeamAvailability.team_id == team_id)
            .order_by(TeamAvailability.day_of_week, TeamAvailability.start_time)
            .all()
        )

        return TeamAvailabilityResponse(
            team_id=team_id,
            team_name=team.name,
            slots=[AvailabilitySlotResponse.model_validate(s) for s in slots],
        )

    def set_team_availability(
        self,
        team_id: int,
        slots: List[AvailabilitySlotCreate],
    ) -> TeamAvailabilityResponse:
        """
        Replace all availability slots for a team (PUT semantics).

        Deletes existing slots and inserts the new set within one transaction.
        """
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise TeamNotFoundError(team_id)

        # Delete old slots
        self.db.query(TeamAvailability).filter(
            TeamAvailability.team_id == team_id
        ).delete()

        # Insert new slots
        new_rows = []
        for slot in slots:
            row = TeamAvailability(
                team_id=team_id,
                day_of_week=slot.day_of_week,
                start_time=slot.start_time,
                end_time=slot.end_time,
                location_preference=slot.location_preference,
            )
            self.db.add(row)
            new_rows.append(row)

        self.db.commit()
        for row in new_rows:
            self.db.refresh(row)

        self._log_operation(
            "Updated availability",
            team_id=team_id,
            slot_count=len(new_rows),
        )

        return TeamAvailabilityResponse(
            team_id=team_id,
            team_name=team.name,
            slots=[AvailabilitySlotResponse.model_validate(r) for r in new_rows],
        )

    # Scoring components, each returns a float in [0, 1]

    @staticmethod
    def _elo_similarity(team: Team, candidate: Team, elo_range: int) -> float:
        """
        Gaussian-decay similarity based on ELO difference.

        Formula:
            ELO(T, O) = exp( - (delta_r)^2 / (2 * sigma^2) )

        where delta_r = |R_T - R_O| and sigma = elo_range / 2.
        This produces a bell-curve centred on delta_r = 0.
        Teams within ~1 sigma get score > 0.60; beyond 2 sigma, score < 0.14.
        """
        r_team = team.rating or 1000
        r_candidate = candidate.rating or 1000
        delta = abs(r_team - r_candidate)
        sigma = elo_range / 2.0
        if sigma == 0:
            return 1.0 if delta == 0 else 0.0
        return math.exp(-(delta ** 2) / (2 * sigma ** 2))

    @staticmethod
    def _geo_proximity(team: Team, candidate: Team) -> float:
        """
        Geographic proximity score using the Haversine formula.

        If both teams have coordinates → Haversine distance.
        If coordinates are missing but cities match → score = 0.8.
        If cities differ and no coordinates → score = 0.0.

        Formula:
            GEO(T, O) = max(0, 1 - d / D_max)

        where d = haversine(T, O) and D_max = 100 km.
        """
        # Both have coordinates — use Haversine
        if (
            team.latitude is not None
            and team.longitude is not None
            and candidate.latitude is not None
            and candidate.longitude is not None
        ):
            d = _haversine(
                team.latitude, team.longitude,
                candidate.latitude, candidate.longitude,
            )
            return max(0.0, 1.0 - d / _MAX_GEO_DISTANCE_KM)

        # Fallback: city-name match
        if team.city and candidate.city:
            if team.city.strip().lower() == candidate.city.strip().lower():
                return 0.8
        return 0.0

    @staticmethod
    def _availability_overlap(
        team: Team, candidate: Team
    ) -> Tuple[float, int]:
        """
        Fraction of the requesting team's slots that overlap with the candidate.

        Two slots overlap when they share the same day_of_week AND their
        time intervals intersect: max(start_a, start_b) < min(end_a, end_b).

        Returns:
            (score, overlap_count) — score in [0, 1], count of overlapping pairs.
        """
        team_slots = team.availability_slots or []
        cand_slots = candidate.availability_slots or []

        if not team_slots:
            # No availability declared — neutral score (don't penalise).
            return 0.5, 0

        overlap_count = 0
        for ts in team_slots:
            for cs in cand_slots:
                if ts.day_of_week != cs.day_of_week:
                    continue
                # Interval intersection check
                latest_start = max(ts.start_time, cs.start_time)
                earliest_end = min(ts.end_time, cs.end_time)
                if latest_start < earliest_end:
                    overlap_count += 1

        score = min(1.0, overlap_count / max(len(team_slots), 1))
        return score, overlap_count

    @staticmethod
    def _recency_penalty(
        candidate_id: int,
        recent_opponents: Dict[int, int],
    ) -> float:
        """
        Penalise opponents that have been played recently.

        Formula:
            RECENCY(O) = min(1, match_count_in_window / 3)

        Playing the same team 3+ times within the recency window gives
        the maximum penalty of 1.0.
        """
        count = recent_opponents.get(candidate_id, 0)
        return min(1.0, count / 3.0)

    @staticmethod
    def _activity_bonus(
        candidate_id: int,
        activity_map: Dict[int, int],
    ) -> float:
        """
        Reward teams that are actively playing on the platform.

        Formula:
            ACTIVITY(O) = min(1, matches_in_window / 5)

        A team with 5+ matches in the activity window gets the full bonus.
        """
        count = activity_map.get(candidate_id, 0)
        return min(1.0, count / 5.0)

    # Data helpers (batch queries to avoid N+1)

    def _get_recent_opponents(self, team_id: int) -> Dict[int, int]:
        """
        Return {opponent_team_id: match_count} for matches within the
        recency window involving *team_id*.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=_RECENCY_WINDOW_DAYS)

        rows = (
            self.db.query(
                Challenge.challenger_id,
                Challenge.opponent_id,
            )
            .filter(
                Challenge.status == ChallengeStatus.COMPLETED,
                Challenge.updated_at >= cutoff,
                or_(
                    Challenge.challenger_id == team_id,
                    Challenge.opponent_id == team_id,
                ),
            )
            .all()
        )

        counts: Dict[int, int] = {}
        for challenger_id, opponent_id in rows:
            other = opponent_id if challenger_id == team_id else challenger_id
            counts[other] = counts.get(other, 0) + 1
        return counts

    def _get_activity_counts(self, team_ids: List[int]) -> Dict[int, int]:
        """
        Return {team_id: completed_match_count} within the activity window
        for the given list of team IDs.
        """
        if not team_ids:
            return {}

        cutoff = datetime.now(timezone.utc) - timedelta(days=_ACTIVITY_WINDOW_DAYS)

        # Count matches where team was challenger
        challenger_counts = (
            self.db.query(
                Challenge.challenger_id,
                func.count(Challenge.id),
            )
            .filter(
                Challenge.status == ChallengeStatus.COMPLETED,
                Challenge.updated_at >= cutoff,
                Challenge.challenger_id.in_(team_ids),
            )
            .group_by(Challenge.challenger_id)
            .all()
        )

        # Count matches where team was opponent
        opponent_counts = (
            self.db.query(
                Challenge.opponent_id,
                func.count(Challenge.id),
            )
            .filter(
                Challenge.status == ChallengeStatus.COMPLETED,
                Challenge.updated_at >= cutoff,
                Challenge.opponent_id.in_(team_ids),
            )
            .group_by(Challenge.opponent_id)
            .all()
        )

        result: Dict[int, int] = {}
        for tid, cnt in challenger_counts:
            result[tid] = result.get(tid, 0) + cnt
        for tid, cnt in opponent_counts:
            result[tid] = result.get(tid, 0) + cnt
        return result


# Utility functions


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two points on a sphere (Haversine formula).

    Parameters are in decimal degrees; returns distance in kilometres.

    Formula:
        a = sin^2(d_lat / 2) + cos(lat1) * cos(lat2) * sin^2(d_lon / 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        d = R * c
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return _EARTH_RADIUS_KM * c
