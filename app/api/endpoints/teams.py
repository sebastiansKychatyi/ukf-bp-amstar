"""
FastAPI endpoints for team management
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    JoinRequestCreate,
    JoinRequestResponse,
    JoinRequestReview,
    TeamCreate,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services.team_service import (
    DuplicateRequestError,
    InsufficientPermissionsError,
    PlayerNotFoundError,
    TeamFullError,
    TeamNotFoundError,
    TeamService,
    TeamServiceError,
)

router = APIRouter(prefix="/teams", tags=["teams"])


# Database session dependency — wire to app.db.session.get_db
async def get_db() -> AsyncSession:
    """Yield an async database session per request."""
    ...


# Authentication dependency — wire to app.core.security.get_current_user
async def get_current_player_id() -> UUID:
    """Return the UUID of the currently authenticated user."""
    ...


# ============================================================================
# TEAM CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Create a new team with the current user as captain

    - **name**: Unique team name (3-100 characters)
    - **captain_id**: Player who will be the team captain
    - **max_players**: Maximum team size (11-50, default: 25)
    - **is_recruiting**: Whether team is accepting join requests
    """
    service = TeamService(db)

    try:
        team = await service.create_team(team_data)
        return team
    except PlayerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a team
    """
    service = TeamService(db)

    try:
        team = await service._get_team(team_id)
        return team
    except TeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Update team information (captain only)

    Only team captains can update team information.
    """
    service = TeamService(db)

    try:
        team = await service.update_team(team_id, team_data, current_player_id)
        return team
    except TeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active members of a team
    """
    ...


# ============================================================================
# JOIN REQUEST ENDPOINTS
# ============================================================================

@router.post("/join-requests", response_model=JoinRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_join_request(
    request_data: JoinRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Request to join a team

    - **team_id**: Team to join
    - **player_id**: Player requesting to join (must match authenticated user)
    - **message**: Optional message to team captain

    The request will be in PENDING status until reviewed by a team captain.
    """
    # Ensure player can only request for themselves
    if request_data.player_id != current_player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only create join requests for yourself"
        )

    service = TeamService(db)

    try:
        join_request = await service.create_join_request(request_data)
        return join_request
    except TeamNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PlayerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateRequestError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except TeamFullError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/join-requests/{team_id}/pending", response_model=List[JoinRequestResponse])
async def get_pending_join_requests(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Get all pending join requests for a team (captain only)

    Only team captains can view pending join requests.
    """
    service = TeamService(db)

    try:
        # Verify requester is captain
        await service._verify_captain(team_id, current_player_id)

        pending_requests = await service.get_pending_requests(team_id)
        return pending_requests
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/join-requests/{request_id}/review", response_model=JoinRequestResponse)
async def review_join_request(
    request_id: UUID,
    review_data: JoinRequestReview,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Approve or reject a join request (captain only)

    - **status**: APPROVED or REJECTED
    - **review_message**: Optional message to the requesting player

    Only team captains can review join requests.
    If approved, the player is automatically added to the team.
    """
    service = TeamService(db)

    try:
        join_request = await service.review_join_request(
            request_id,
            review_data,
            current_player_id
        )
        return join_request
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TeamFullError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# TEAM MEMBER MANAGEMENT ENDPOINTS
# ============================================================================

@router.delete("/{team_id}/members/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    player_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Remove a player from a team

    Can be done by:
    - Team captain (can remove any member)
    - The player themselves (leave team)

    Cannot remove the last captain from a team.
    """
    service = TeamService(db)

    try:
        await service.remove_team_member(team_id, player_id, current_player_id)
        return None
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{team_id}/members/{player_id}/promote", status_code=status.HTTP_200_OK)
async def promote_to_captain(
    team_id: UUID,
    player_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_player_id: UUID = Depends(get_current_player_id)
):
    """
    Promote a team member to captain (captain only)

    Teams can have multiple captains.
    Only existing captains can promote members.
    """
    service = TeamService(db)

    try:
        await service.assign_captain(team_id, player_id, current_player_id)
        return {"message": "Player promoted to captain successfully"}
    except InsufficientPermissionsError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except TeamServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
