"""Challenge API endpoints — full CRUD and state machine transitions."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user, get_current_captain
from app.models.user import User
from app.models.challenge import ChallengeStatus
from app.services.challenge_service import ChallengeService
from app.services.elo_service import EloService
from app.schemas.challenge import (
    ChallengeCreate,
    ChallengeResponse,
    ChallengeListResponse,
    ChallengeResultSubmit,
    ChallengeCompleteResponse,
)
from app.core.exceptions import (
    ChallengeNotFoundError,
    TeamNotFoundError,
    SelfChallengeError,
    InvalidChallengeStatusError,
    NotTeamOwnerError,
    InsufficientPermissionsError,
)

router = APIRouter()


def _handle(exc: Exception):
    """Map domain exceptions to HTTP responses."""
    if isinstance(exc, ChallengeNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, TeamNotFoundError):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message)
    if isinstance(exc, SelfChallengeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message)
    if isinstance(exc, InvalidChallengeStatusError):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=exc.message)
    if isinstance(exc, (NotTeamOwnerError, InsufficientPermissionsError)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=exc.message)
    raise exc


@router.get("/", response_model=ChallengeListResponse, summary="List challenges with optional filters")
def list_challenges(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[ChallengeStatus] = Query(None, alias="status"),
    team_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    """
    Return a paginated list of challenges.

    Filters:
    - **status**: `pending` | `accepted` | `rejected` | `completed` | `cancelled`
    - **team_id**: only challenges involving this team
    """
    svc = ChallengeService(db)
    items, total = svc.get_challenges(skip=skip, limit=limit, status=status_filter, team_id=team_id)
    return ChallengeListResponse(
        items=[ChallengeResponse.model_validate(c) for c in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/my", response_model=ChallengeListResponse, summary="Get challenges for the current user's team")
def my_challenges(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all challenges involving the current user's team."""
    from app.models.team import Team
    team = db.query(Team).filter(Team.captain_id == current_user.id).first()
    if not team:
        from app.models.team_member import TeamMember
        membership = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first()
        if not membership:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="You are not part of any team")
        team_id = membership.team_id
    else:
        team_id = team.id

    svc = ChallengeService(db)
    items, total = svc.get_team_challenges(team_id, skip=skip, limit=limit)
    return ChallengeListResponse(
        items=[ChallengeResponse.model_validate(c) for c in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{challenge_id}", response_model=ChallengeResponse, summary="Get challenge details")
def get_challenge(challenge_id: int, db: Session = Depends(get_db)):
    """Return full details of a specific challenge."""
    svc = ChallengeService(db)
    try:
        challenge = svc.get_challenge(challenge_id)
    except ChallengeNotFoundError as e:
        _handle(e)
    return ChallengeResponse.model_validate(challenge)


@router.post(
    "/",
    response_model=ChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new challenge (captain only)",
)
def create_challenge(
    payload: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """
    Captain creates a challenge targeting another team.

    - Cannot challenge your own team
    - Cannot have duplicate pending challenges between the same teams
    """
    svc = ChallengeService(db)
    try:
        challenge = svc.create_challenge(
            challenger_captain_id=current_user.id,
            opponent_id=payload.opponent_id,
            match_date=payload.match_date,
            location=payload.location,
        )
    except (TeamNotFoundError, SelfChallengeError, InvalidChallengeStatusError) as e:
        _handle(e)
    return ChallengeResponse.model_validate(challenge)


@router.put("/{challenge_id}/accept", response_model=ChallengeResponse, summary="Accept a challenge (opponent captain only)")
def accept_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """Transition: PENDING → ACCEPTED."""
    svc = ChallengeService(db)
    try:
        challenge = svc.accept_challenge(challenge_id, current_user.id)
    except (ChallengeNotFoundError, NotTeamOwnerError, InvalidChallengeStatusError) as e:
        _handle(e)
    return ChallengeResponse.model_validate(challenge)


@router.put("/{challenge_id}/reject", response_model=ChallengeResponse, summary="Reject a challenge (opponent captain only)")
def reject_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """Transition: PENDING → REJECTED."""
    svc = ChallengeService(db)
    try:
        challenge = svc.reject_challenge(challenge_id, current_user.id)
    except (ChallengeNotFoundError, NotTeamOwnerError, InvalidChallengeStatusError) as e:
        _handle(e)
    return ChallengeResponse.model_validate(challenge)


@router.put("/{challenge_id}/cancel", response_model=ChallengeResponse, summary="Cancel a challenge (challenger captain only)")
def cancel_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_captain),
):
    """Transition: PENDING | ACCEPTED → CANCELLED."""
    svc = ChallengeService(db)
    try:
        challenge = svc.cancel_challenge(challenge_id, current_user.id)
    except (ChallengeNotFoundError, NotTeamOwnerError, InvalidChallengeStatusError) as e:
        _handle(e)
    return ChallengeResponse.model_validate(challenge)


@router.put("/{challenge_id}/result", response_model=ChallengeCompleteResponse, summary="Submit match result and trigger ELO update")
def submit_result(
    challenge_id: int,
    payload: ChallengeResultSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Record scores and complete the challenge (ACCEPTED → COMPLETED).

    Automatically triggers ELO recalculation for both teams.
    Either team's captain may submit.
    """
    challenge_svc = ChallengeService(db)
    elo_svc = EloService(db)

    try:
        challenge = challenge_svc.submit_result(
            challenge_id=challenge_id,
            user_id=current_user.id,
            challenger_score=payload.challenger_score,
            opponent_score=payload.opponent_score,
        )
    except (ChallengeNotFoundError, InvalidChallengeStatusError, InsufficientPermissionsError) as e:
        _handle(e)

    # ELO is computed only after both captains confirm (COMPLETED state)
    elo_updates = []
    if challenge.status == ChallengeStatus.COMPLETED:
        update_a, update_b = elo_svc.update_ratings(challenge_id)
        elo_updates = [update_a, update_b]

    return ChallengeCompleteResponse(
        challenge=ChallengeResponse.model_validate(challenge),
        elo_updates=elo_updates,
    )
