"""
Platform-wide aggregate statistics endpoint.

Public — no authentication required — so the landing page can display
live counters for guests who have not yet logged in.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.team import Team
from app.models.challenge import Challenge, ChallengeStatus

router = APIRouter()


class GlobalStats(BaseModel):
    """Aggregate platform counters displayed on the public landing page."""
    total_users: int
    total_teams: int
    completed_matches: int
    total_challenges: int


@router.get(
    "/global",
    response_model=GlobalStats,
    summary="Platform-wide statistics (public)",
)
def get_global_stats(db: Session = Depends(get_db)):
    """
    Return aggregate counts for the landing page.

    No authentication required — intentionally public so visitors can see
    that the platform is active before they register.
    """
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_teams = db.query(func.count(Team.id)).scalar() or 0
    completed_matches = (
        db.query(func.count(Challenge.id))
        .filter(Challenge.status == ChallengeStatus.COMPLETED)
        .scalar()
    ) or 0
    total_challenges = db.query(func.count(Challenge.id)).scalar() or 0

    return GlobalStats(
        total_users=total_users,
        total_teams=total_teams,
        completed_matches=completed_matches,
        total_challenges=total_challenges,
    )
