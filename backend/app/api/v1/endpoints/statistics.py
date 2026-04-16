"""
Player Statistics API Endpoints

Provides per-match stat recording, aggregated stats, leaderboards,
and player profile queries.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_captain
from app.models.user import User
from app.services.statistics_service import StatisticsService
from app.schemas.player_statistics import (
    MatchPlayerStatisticsCreate,
    MatchPlayerStatisticsResponse,
    PlayerStatisticsResponse,
    PlayerProfileWithStats,
)
from app.core.exceptions import (
    ChallengeNotFoundError,
    UserNotFoundError,
    BusinessRuleViolationError,
)

router = APIRouter()


# Match statistics endpoints


@router.post(
    "/match/{challenge_id}",
    response_model=List[MatchPlayerStatisticsResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record per-player stats for a completed match",
)
def record_match_stats(
    challenge_id: int,
    stats: List[MatchPlayerStatisticsCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """
    Submit per-player statistics for a completed challenge.

    Validates:
    - Challenge must be COMPLETED
    - Each player's team must be a participant in the challenge
    - No duplicate entries for the same player/challenge
    """
    svc = StatisticsService(db)
    try:
        return svc.record_match_stats(challenge_id, stats)
    except ChallengeNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Challenge {challenge_id} not found",
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=e.message)


# Player stats and profiles


@router.get(
    "/player/{user_id}",
    response_model=PlayerProfileWithStats,
    summary="Get player profile with aggregated stats",
)
def get_player_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Full player profile including team info and lifetime statistics."""
    svc = StatisticsService(db)
    try:
        return svc.get_player_profile(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )


@router.get(
    "/player/{user_id}/matches",
    response_model=List[MatchPlayerStatisticsResponse],
    summary="Get per-match stats for a player",
)
def get_player_match_stats(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Per-match breakdown for a player, newest first."""
    svc = StatisticsService(db)
    rows = svc.get_player_match_history(user_id, skip=skip, limit=limit)
    return [MatchPlayerStatisticsResponse.model_validate(r) for r in rows]


# Leaderboards


@router.get(
    "/top-scorers",
    summary="Top players by goals scored",
)
def top_scorers(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Leaderboard of players ranked by total goals."""
    svc = StatisticsService(db)
    return svc.get_top_scorers(limit=limit)


@router.get(
    "/top-assists",
    summary="Top players by assists",
)
def top_assists(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Leaderboard of players ranked by total assists."""
    svc = StatisticsService(db)
    return svc.get_top_assists(limit=limit)
