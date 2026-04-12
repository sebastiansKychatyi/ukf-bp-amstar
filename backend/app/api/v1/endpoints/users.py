"""
User profile endpoints.

Provides:
  GET  /users/me                  — current user profile
  PATCH /users/me                 — update full_name / email
  POST /users/me/change-password  — change password (requires current password)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.crud.user import user as crud_user
from app.core.security import verify_password, get_password_hash

router = APIRouter()


# Input schemas (small, endpoint-specific — no need for a separate file)

class ProfileUpdate(BaseModel):
    """Fields the user may update on their own profile."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Payload for changing the authenticated user's password."""
    current_password: str
    new_password: str


# Endpoints

@router.get("/me", response_model=UserSchema, summary="Get current user profile")
def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserSchema, summary="Update profile")
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update full_name and/or email for the authenticated user.

    Email uniqueness is enforced — a 409 is returned if the address is
    already registered by a different account.
    """
    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.email is not None:
        existing = crud_user.get_by_email(db, email=payload.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Email already registered by another account",
            )
        current_user.email = payload.email

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Change password for the authenticated user.

    Requires the current password for verification.
    New password must be at least 8 characters.
    """
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    if len(payload.new_password) < 8:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 8 characters",
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
