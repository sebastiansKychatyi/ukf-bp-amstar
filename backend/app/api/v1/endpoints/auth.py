import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.api.deps import get_db, get_current_active_user, oauth2_scheme
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.core.redis import redis_client
from app.crud.user import user as crud_user
from app.schemas.token import Token
from app.schemas.user import User, UserCreate
from app.models.user import User as UserModel
from app.models.password_reset import PasswordResetToken

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    user = crud_user.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud_user.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme)
):
    """
    Logout by blacklisting the current token.
    The token will remain invalid until it expires.
    """
    try:
        # Decode token to get expiration time
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")

        if exp:
            # Calculate remaining TTL for the token
            current_time = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - current_time)

            if ttl > 0:
                # Add token to blacklist with remaining TTL
                redis_client.blacklist_token(token, ttl)

        return {"message": "Successfully logged out"}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ── Password Reset ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset token.

    Always returns 200 to avoid revealing whether the email is registered.
    In development the token is printed to the server console; in production
    this would trigger an email via an SMTP service.
    """
    user = crud_user.get_by_email(db, email=payload.email)
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires,
        )
        db.add(db_token)
        db.commit()
        # In production: send an email. For now, log to console.
        print(f"\n[PASSWORD RESET] Token for '{user.email}': {token}\n", flush=True)

    return {"message": "If that email is registered, a reset token has been generated. Check server logs."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Consume a password reset token and set a new password.

    Returns 400 if the token is invalid, already used, or expired.
    """
    if len(payload.new_password) < 8:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 8 characters",
        )

    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used == False,  # noqa: E712
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.query(UserModel).filter(UserModel.id == record.user_id).first()
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    record.used = True
    db.commit()

    return {"message": "Password has been reset successfully. You can now log in with your new password."}
