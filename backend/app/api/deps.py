from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.redis import redis_client
from app.db.session import get_db
from app.models.user import User, UserRole
from app.crud.user import user as crud_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if token is blacklisted
    if redis_client.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud_user.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory to require specific user roles

    Usage:
        @router.get("/captain-only")
        def captain_route(user: User = Depends(require_role(UserRole.CAPTAIN))):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join([r.value for r in allowed_roles])}"
            )
        return current_user
    return role_checker


# Convenience dependencies for specific roles
def get_current_captain(current_user: User = Depends(get_current_active_user)) -> User:
    """Require CAPTAIN role"""
    if current_user.role != UserRole.CAPTAIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Captain role required"
        )
    return current_user


def get_current_referee(current_user: User = Depends(get_current_active_user)) -> User:
    """Require REFEREE role"""
    if current_user.role != UserRole.REFEREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Referee role required"
        )
    return current_user
