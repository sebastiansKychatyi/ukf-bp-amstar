"""
Admin-only endpoints for platform management.

All mutating routes require is_superuser == True.
The GET /admin/announcement endpoint is intentionally public so the frontend
can fetch the current banner without an auth token.

The global announcement is stored as a module-level variable — ephemeral
(resets on process restart). Acceptable for a demo; production would
persist this in a dedicated DB table.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_superuser
from app.models.user import User as UserModel
from app.models.team import Team as TeamModel
from app.models.challenge import Challenge as ChallengeModel
from app.models.tournament import TournamentParticipant, Tournament as TournamentModel
from app.models.notification import Notification
from app.models.password_reset import PasswordResetToken
from app.models.team_member import TeamMember
from app.models.player_statistics import PlayerStatistics
from app.models.rating import Rating
from app.schemas.user import User as UserSchema
from app.schemas.team import TeamResponse

router = APIRouter()

# Module-level announcement, resets on process restart
_announcement: Optional[str] = None


class AnnouncementPayload(BaseModel):
    message: Optional[str] = None


# User management

@router.get("/users", response_model=List[UserSchema])
def list_users(
    db: Session = Depends(get_db),
    _: UserModel = Depends(get_current_superuser),
):
    """Return all registered users ordered by ID."""
    return db.query(UserModel).order_by(UserModel.id).all()


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: UserModel = Depends(get_current_superuser),
):
    """Disable login for a user (soft ban). Cannot deactivate yourself."""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
    target = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    target.is_active = False
    db.commit()
    return {"message": f"User '{target.username}' has been deactivated"}


@router.patch("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: UserModel = Depends(get_current_superuser),
):
    """Re-enable a previously deactivated user."""
    target = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    target.is_active = True
    db.commit()
    return {"message": f"User '{target.username}' has been activated"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: UserModel = Depends(get_current_superuser),
):
    """Permanently delete a user account. Cannot delete yourself."""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    target = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    # Remove from team membership
    db.query(TeamMember).filter(TeamMember.user_id == user_id).delete(synchronize_session=False)

    # Delete notifications
    db.query(Notification).filter(Notification.user_id == user_id).delete(synchronize_session=False)

    # Delete password reset tokens
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete(synchronize_session=False)

    # Delete player statistics
    db.query(PlayerStatistics).filter(PlayerStatistics.user_id == user_id).delete(synchronize_session=False)

    # Reassign tournaments created by this user to the admin performing the delete
    db.query(TournamentModel).filter(TournamentModel.created_by_id == user_id).update(
        {"created_by_id": admin.id}, synchronize_session=False
    )

    # Delete teams where this user is captain (cascades members/join requests)
    captain_teams = db.query(TeamModel).filter(TeamModel.captain_id == user_id).all()
    for team in captain_teams:
        db.query(TournamentParticipant).filter(
            TournamentParticipant.team_id == team.id
        ).delete(synchronize_session=False)
        challenge_ids = [c.id for c in db.query(ChallengeModel.id).filter(
            (ChallengeModel.challenger_id == team.id) | (ChallengeModel.opponent_id == team.id)
        ).all()]
        if challenge_ids:
            db.query(Rating).filter(Rating.challenge_id.in_(challenge_ids)).delete(synchronize_session=False)
        db.query(ChallengeModel).filter(
            (ChallengeModel.challenger_id == team.id) | (ChallengeModel.opponent_id == team.id)
        ).delete(synchronize_session=False)
        db.delete(team)

    db.flush()
    db.delete(target)
    db.commit()


# Team management

@router.get("/teams", response_model=List[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    _: UserModel = Depends(get_current_superuser),
):
    """Return all teams ordered by ID."""
    return db.query(TeamModel).order_by(TeamModel.id).all()


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    _: UserModel = Depends(get_current_superuser),
):
    """Permanently delete a team and cascade to related records."""
    target = db.query(TeamModel).filter(TeamModel.id == team_id).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Delete tournament participations for this team
    db.query(TournamentParticipant).filter(
        TournamentParticipant.team_id == team_id
    ).delete(synchronize_session=False)

    # Delete rating records that reference challenges of this team
    challenge_ids = [c.id for c in db.query(ChallengeModel.id).filter(
        (ChallengeModel.challenger_id == team_id) | (ChallengeModel.opponent_id == team_id)
    ).all()]
    if challenge_ids:
        db.query(Rating).filter(Rating.challenge_id.in_(challenge_ids)).delete(synchronize_session=False)

    # Delete challenges that reference this team
    db.query(ChallengeModel).filter(
        (ChallengeModel.challenger_id == team_id) | (ChallengeModel.opponent_id == team_id)
    ).delete(synchronize_session=False)

    db.delete(target)
    db.commit()


# Announcement endpoints

@router.get("/announcement")
def get_announcement():
    """Return the current global announcement. Public — no auth required."""
    return {"message": _announcement}


@router.post("/announcement")
def set_announcement(
    payload: AnnouncementPayload,
    _: UserModel = Depends(get_current_superuser),
):
    """Set or clear the global announcement banner."""
    global _announcement
    _announcement = payload.message or None
    return {"message": _announcement}
