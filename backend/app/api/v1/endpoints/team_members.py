"""
Team Members API Endpoints

Handles team roster management including:
- Viewing team roster
- Removing members
- Updating member info
- Transferring captaincy
- Leaving a team
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.db.session import get_db
from app.models.user import UserRole
from app.services.team_member_service import TeamMemberService


router = APIRouter()


# DEPENDENCY INJECTION


def get_team_member_service(db: Session = Depends(get_db)) -> TeamMemberService:
    """Dependency injection for TeamMemberService"""
    return TeamMemberService(db)


# TEAM ROSTER ENDPOINTS


@router.get("/{team_id}/members", response_model=List[schemas.TeamMemberResponse])
def get_team_roster(
    *,
    team_id: int,
    service: TeamMemberService = Depends(get_team_member_service)
) -> List[models.TeamMember]:
    """
    Get all members of a team

    **Public Endpoint** - No authentication required

    Returns list of team members with their:
    - User info (username, full_name)
    - Role (CAPTAIN/PLAYER)
    - Position
    - Jersey number
    - Join date

    **Raises:**
    - 404: Team not found
    """
    members = service.get_team_roster(team_id)
    return members


@router.get("/{team_id}/members/{user_id}", response_model=schemas.TeamMemberResponse)
def get_team_member(
    *,
    team_id: int,
    user_id: int,
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.TeamMember:
    """
    Get a specific team member

    **Raises:**
    - 404: Team or member not found
    """
    from app.core.exceptions import PlayerNotInTeamError

    member = service.get_member(team_id, user_id)
    if not member:
        raise PlayerNotInTeamError(user_id, team_id)
    return member


@router.delete("/{team_id}/members/{user_id}", response_model=schemas.TeamMemberResponse)
def remove_team_member(
    *,
    team_id: int,
    user_id: int,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.TeamMember:
    """
    Remove a member from the team (Captain only)

    **Business Rules:**
    - Only team captain can remove members
    - Captain cannot remove themselves

    **Raises:**
    - 403: Not team owner
    - 404: Team or member not found
    - 400: Cannot remove captain
    """
    member = service.remove_member(
        team_id=team_id,
        user_id=user_id,
        captain_id=current_user.id
    )
    return member


@router.put("/{team_id}/members/{user_id}", response_model=schemas.TeamMemberResponse)
def update_team_member(
    *,
    team_id: int,
    user_id: int,
    member_update: schemas.TeamMemberUpdate,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.TeamMember:
    """
    Update team member info (Captain only)

    **Updatable Fields:**
    - position: Playing position (GK, DEF, MID, FWD)
    - jersey_number: Jersey number (1-99)

    **Raises:**
    - 403: Not team owner
    - 404: Team or member not found
    """
    member = service.update_member(
        team_id=team_id,
        user_id=user_id,
        captain_id=current_user.id,
        position=member_update.position,
        jersey_number=member_update.jersey_number
    )
    return member


@router.post("/{team_id}/leave", status_code=status.HTTP_200_OK)
def leave_team(
    *,
    team_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> dict:
    """
    Leave a team (Player only)

    **Business Rules:**
    - Captain cannot leave (must transfer captaincy first)

    **Raises:**
    - 400: Captain cannot leave
    - 404: Not a team member
    """
    service.leave_team(team_id=team_id, user_id=current_user.id)
    return {"message": "Successfully left the team"}


@router.post("/{team_id}/transfer-captaincy/{new_captain_id}", response_model=schemas.Team)
def transfer_captaincy(
    *,
    team_id: int,
    new_captain_id: int,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.Team:
    """
    Transfer team captaincy to another member

    **Business Rules:**
    - Only current captain can transfer
    - New captain must be a team member

    **Raises:**
    - 403: Not team owner
    - 404: New captain not in team
    """
    team = service.transfer_captaincy(
        team_id=team_id,
        current_captain_id=current_user.id,
        new_captain_id=new_captain_id
    )
    return team


# MY TEAM ENDPOINTS (for authenticated users)


@router.get("/my/membership", response_model=schemas.TeamMemberResponse)
def get_my_membership(
    *,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.TeamMember:
    """
    Get current user's team membership info

    **Raises:**
    - 404: User is not in any team
    """
    from app.core.exceptions import PlayerNotInTeamError

    # Find user's team membership
    membership = service.db.query(models.TeamMember)\
        .filter(models.TeamMember.user_id == current_user.id)\
        .first()

    if not membership:
        raise PlayerNotInTeamError(current_user.id)

    return membership


@router.get("/my/team", response_model=schemas.Team)
def get_my_team_as_member(
    *,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.Team:
    """
    Get the team the current user belongs to

    Works for both captains and players.

    **Raises:**
    - 404: User is not in any team
    """
    from app.core.exceptions import TeamNotFoundError

    team = service.get_user_team(current_user.id)
    if not team:
        raise TeamNotFoundError(f"user_{current_user.id}")

    return team
