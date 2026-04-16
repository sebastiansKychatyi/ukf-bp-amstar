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
