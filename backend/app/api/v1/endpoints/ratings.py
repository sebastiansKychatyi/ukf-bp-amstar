"""
Ratings API Endpoints

Provides the ELO leaderboard and per-team rating history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.elo_service import EloService
from app.core.exceptions import TeamNotFoundError

router = APIRouter()


@router.get(
    "/leaderboard",
    summary="Get team leaderboard ranked by ELO",
)
def get_leaderboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Return all teams ranked by ELO rating (descending).

    Each entry includes rank, team name, city, rating, and matches played.
    """
    svc = EloService(db)
    return svc.get_leaderboard(skip=skip, limit=limit)


@router.get(
    "/team/{team_id}/history",
    summary="Get rating history for a team",
)
def get_rating_history(
    team_id: int,
    db: Session = Depends(get_db),
):
    """
    Return chronological rating changes for a team.

    Useful for rendering a rating-progression chart on the frontend.
    Each entry has: challenge_id, old_rating, new_rating, rating_change, date.
    """
    svc = EloService(db)
    try:
        return svc.get_rating_history(team_id)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found",
        )
