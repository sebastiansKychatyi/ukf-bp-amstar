"""
Matchmaking API Endpoints

Provides:
- POST /matchmaking/find-opponent       — Run the matchmaking algorithm
- GET  /matchmaking/team/{id}/availability — Get a team's availability
- PUT  /matchmaking/team/{id}/availability — Set a team's availability (captain only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_captain
from app.models.user import User
from app.models.team_member import TeamMember
from app.services.matchmaking_service import MatchmakingService
from app.schemas.matchmaking import (
    MatchmakingResponse,
    MatchmakingConfig,
    TeamAvailabilityResponse,
    TeamAvailabilityUpdate,
)
from app.core.exceptions import TeamNotFoundError, NotTeamOwnerError

router = APIRouter()


# Matchmaking endpoints


@router.post(
    "/find-opponent",
    response_model=MatchmakingResponse,
    summary="Find best opponents for your team",
)
def find_opponent(
    config: MatchmakingConfig = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """
    Run the Smart Matchmaking Algorithm for the captain's team.

    Evaluates all other teams and returns a ranked list of suggested
    opponents sorted by composite matchmaking score.

    Optionally accepts weight overrides for experimentation.
    """
    service = MatchmakingService(db)

    # Find the captain's team
    team = _get_captain_team(db, current_user.id)

    return service.find_opponents(team.id, config)


@router.post(
    "/find-opponent/{team_id}",
    response_model=MatchmakingResponse,
    summary="Find best opponents for a specific team (any authenticated user)",
)
def find_opponent_for_team(
    team_id: int,
    config: MatchmakingConfig = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Run the matchmaking algorithm for a specific team.
    Useful for viewing suggestions without being the captain.
    """
    service = MatchmakingService(db)
    return service.find_opponents(team_id, config)


# Team availability endpoints


@router.get(
    "/team/{team_id}/availability",
    response_model=TeamAvailabilityResponse,
    summary="Get a team's availability schedule",
)
def get_team_availability(
    team_id: int,
    db: Session = Depends(get_db),
):
    """Get the weekly availability slots for a team (public)."""
    service = MatchmakingService(db)
    try:
        return service.get_team_availability(team_id)
    except TeamNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found",
        )


@router.put(
    "/team/{team_id}/availability",
    response_model=TeamAvailabilityResponse,
    summary="Set team availability (captain only)",
)
def set_team_availability(
    team_id: int,
    payload: TeamAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """
    Replace all availability slots for a team.

    Only the team captain can update availability.
    Sends the full list of desired slots; old slots are replaced.
    """
    service = MatchmakingService(db)

    # Verify ownership
    from app.models.team import Team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found",
        )
    if team.captain_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team captain can update availability",
        )

    return service.set_team_availability(team_id, payload.slots)


# Helpers


def _get_captain_team(db: Session, user_id: int):
    """Find the team owned by this captain."""
    from app.models.team import Team
    team = db.query(Team).filter(Team.captain_id == user_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a team. Create one first.",
        )
    return team
