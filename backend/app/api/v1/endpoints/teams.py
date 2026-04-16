"""
Team API Endpoints

Handles team CRUD operations, statistics, match history, and roster:
- Listing and searching teams
- Creating, updating, and deleting teams (Captain only)
- Viewing team stats and match history
- Viewing team roster with player statistics

All business logic is delegated to TeamService (Separation of Concerns).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_captain, get_current_active_user
from app.schemas.team import (
    Team, TeamCreate, TeamUpdate, TeamDetailResponse,
    MatchHistoryItem, TeamStatsSummary,
)
from app.schemas.team_member import TeamMemberWithStats
from app.models.user import User
from app.services.team_service import TeamService


router = APIRouter()


# Dependencies


def get_team_service(db: Session = Depends(get_db)) -> TeamService:
    """Dependency injection for TeamService."""
    return TeamService(db)


# Team retrieval endpoints


@router.get("/", response_model=List[Team])
def get_teams(
    skip: int = 0,
    limit: int = 100,
    service: TeamService = Depends(get_team_service),
):
    """Get all teams with pagination."""
    return service.get_teams(skip=skip, limit=limit)


@router.get("/my/team", response_model=Optional[TeamDetailResponse])
def get_my_team(
    current_user: User = Depends(get_current_active_user),
    service: TeamService = Depends(get_team_service),
):
    """
    Get the current user's team.

    Works for both captains (team they own) and players (team they belong to).
    Returns null (200) when the user is not part of any team.
    """
    try:
        return service.get_my_team(user_id=current_user.id)
    except Exception:
        return None


@router.get("/{team_id}", response_model=TeamDetailResponse)
def get_team(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    """Get a specific team by ID with captain info."""
    return service.get_team_by_id(team_id)


@router.get("/{team_id}/stats", response_model=TeamStatsSummary)
def get_team_stats(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    """Get aggregated statistics for a team from completed challenges."""
    return service.get_team_stats(team_id)


@router.get("/{team_id}/matches", response_model=List[MatchHistoryItem])
def get_team_match_history(
    team_id: int,
    skip: int = 0,
    limit: int = 20,
    service: TeamService = Depends(get_team_service),
):
    """Get match history for a team (completed and accepted challenges)."""
    return service.get_team_match_history(team_id, skip=skip, limit=limit)


@router.get("/{team_id}/roster-stats", response_model=List[TeamMemberWithStats])
def get_team_roster_with_stats(
    team_id: int,
    service: TeamService = Depends(get_team_service),
):
    """Get team roster with player statistics."""
    return service.get_team_roster_with_stats(team_id)


# Team mutation endpoints (captain only)


@router.post("/", response_model=Team, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    current_user: User = Depends(get_current_captain),
    service: TeamService = Depends(get_team_service),
):
    """
    Create a new team.

    **CAPTAIN role required.**
    Each captain can only create ONE team.
    Captain is automatically added as a team member.
    """
    return service.create_team(team_in=team_in, captain_id=current_user.id)


@router.put("/{team_id}", response_model=Team)
def update_team(
    team_id: int,
    team_in: TeamUpdate,
    current_user: User = Depends(get_current_captain),
    service: TeamService = Depends(get_team_service),
):
    """
    Update a team.

    **CAPTAIN role required** and you must be the captain of this team.
    """
    return service.update_team(
        team_id=team_id,
        team_in=team_in,
        current_user_id=current_user.id,
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_captain),
    service: TeamService = Depends(get_team_service),
):
    """
    Delete a team.

    **CAPTAIN role required** and you must be the captain of this team.
    Removes all team members and pending join requests.
    """
    service.delete_team(team_id=team_id, current_user_id=current_user.id)
    return None
