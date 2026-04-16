from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    # Use str so Pydantic does not re-validate emails already stored in the DB.
    # Input validation (registration) is handled separately in UserCreate.
    email: str
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.PLAYER

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        from email_validator import validate_email, EmailNotValidError
        try:
            info = validate_email(v, check_deliverability=False)
            return info.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in [UserRole.PLAYER, UserRole.CAPTAIN, UserRole.REFEREE]:
            raise ValueError('Invalid role. Must be PLAYER, CAPTAIN, or REFEREE')
        return v


class UserUpdate(UserBase):
    password: Optional[str] = None
    # Note: role is NOT included here because roles are permanent (cannot be changed)


class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """User schema for API responses"""
    pass


class UserRead(User):
    """Alias for User schema - used for response models"""
    pass
