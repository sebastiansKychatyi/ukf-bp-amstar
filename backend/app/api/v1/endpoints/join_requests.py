"""
Join Request API Endpoints

Handles player join request workflow:
- Creating join requests (players)
- Viewing pending requests (captains)
- Accepting/Rejecting requests (captains)
- Viewing own requests (players)
- Cancelling requests (players)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.db.session import get_db
from app.models.user import UserRole
from app.models.join_request import JoinRequestStatus
from app.services.team_member_service import TeamMemberService


router = APIRouter()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_team_member_service(db: Session = Depends(get_db)) -> TeamMemberService:
    """Dependency injection for TeamMemberService"""
    return TeamMemberService(db)


# ============================================================================
# PLAYER ENDPOINTS - Join Request Management
# ============================================================================


@router.post("/", response_model=schemas.JoinRequestResponse, status_code=status.HTTP_201_CREATED)
def create_join_request(
    *,
    request_in: schemas.JoinRequestCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.JoinRequest:
    """
    Create a join request to join a team

    **Business Rules:**
    - Player cannot be already in a team
    - Player cannot have pending request for same team

    **Request Body:**
    ```json
    {
      "team_id": 1,
      "message": "I would like to join your team!",
      "position": "MID"
    }
    ```

    **Raises:**
    - 400: Player already in a team
    - 400: Pending request already exists
    - 404: Team not found
    """
    try:
        join_request = service.create_join_request(
            team_id=request_in.team_id,
            user_id=current_user.id,
            message=request_in.message,
            position=request_in.position
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A join request for this team already exists.",
        )
    return join_request


@router.get("/my", response_model=List[schemas.MyJoinRequestResponse])
def get_my_join_requests(
    *,
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> List[models.JoinRequest]:
    """
    Get all join requests made by the current user

    Returns requests with their status and team info.
    Useful for players to track their pending applications.
    """
    requests = service.get_user_join_requests(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return requests


@router.delete("/{request_id}", response_model=schemas.JoinRequestResponse)
def cancel_join_request(
    *,
    request_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.JoinRequest:
    """
    Cancel a pending join request

    **Business Rules:**
    - Only the requesting player can cancel
    - Only PENDING requests can be cancelled

    **Raises:**
    - 403: Not the requester
    - 400: Request is not pending
    - 404: Request not found
    """
    request = service.cancel_join_request(
        request_id=request_id,
        user_id=current_user.id
    )
    return request


# ============================================================================
# CAPTAIN ENDPOINTS - Review Join Requests
# ============================================================================


@router.get("/team/{team_id}/pending", response_model=List[schemas.JoinRequestResponse])
def get_pending_requests(
    *,
    team_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    service: TeamMemberService = Depends(get_team_member_service)
) -> List[models.JoinRequest]:
    """
    Get pending join requests for a team (Captain only)

    Returns all pending requests with player info for review.

    **Raises:**
    - 403: Not team owner
    - 404: Team not found
    """
    requests = service.get_pending_requests(
        team_id=team_id,
        captain_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return requests


@router.post("/{request_id}/review", response_model=schemas.JoinRequestResponse)
def review_join_request(
    *,
    request_id: int,
    review: schemas.JoinRequestReview,
    current_user: models.User = Depends(deps.require_role(UserRole.CAPTAIN)),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.JoinRequest:
    """
    Accept or reject a join request (Captain only)

    **Business Rules:**
    - Only team captain can review
    - Request must be in PENDING status
    - If accepted, player is automatically added to team

    **Request Body:**
    ```json
    {
      "status": "ACCEPTED",
      "review_message": "Welcome to the team!"
    }
    ```

    or

    ```json
    {
      "status": "REJECTED",
      "review_message": "Sorry, the roster is full."
    }
    ```

    **Raises:**
    - 403: Not team owner
    - 400: Invalid status transition
    - 400: Player already in a team (when accepting)
    - 404: Request not found
    """
    # Validate status is ACCEPTED or REJECTED
    if review.status not in [JoinRequestStatus.ACCEPTED, JoinRequestStatus.REJECTED]:
        from app.core.exceptions import InvalidJoinRequestStatusError
        raise InvalidJoinRequestStatusError(
            current_status="PENDING",
            attempted_status=review.status.value
        )

    # Convert schema enum to model enum
    model_status = JoinRequestStatus(review.status.value)

    request = service.review_join_request(
        request_id=request_id,
        captain_id=current_user.id,
        status=model_status,
        review_message=review.review_message
    )
    return request


# ============================================================================
# CONVENIENCE ENDPOINTS
# ============================================================================


@router.get("/{request_id}", response_model=schemas.JoinRequestResponse)
def get_join_request(
    *,
    request_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    service: TeamMemberService = Depends(get_team_member_service)
) -> models.JoinRequest:
    """
    Get a specific join request

    User can only see their own requests or requests for teams they captain.

    **Raises:**
    - 403: Not authorized to view
    - 404: Request not found
    """
    from sqlalchemy.orm import joinedload
    from app.core.exceptions import JoinRequestNotFoundError, InsufficientPermissionsError

    request = service.db.query(models.JoinRequest)\
        .options(
            joinedload(models.JoinRequest.user),
            joinedload(models.JoinRequest.team)
        )\
        .filter(models.JoinRequest.id == request_id)\
        .first()

    if not request:
        raise JoinRequestNotFoundError(request_id)

    # Check authorization: must be requester or team captain
    is_requester = request.user_id == current_user.id
    is_captain = request.team.captain_id == current_user.id

    if not is_requester and not is_captain:
        raise InsufficientPermissionsError()

    return request
