"""
Join Request Schemas

Pydantic schemas for team join request operations.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class JoinRequestStatus(str, Enum):
    """Status of a join request"""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class JoinRequestCreate(BaseModel):
    """Schema for creating a join request"""
    team_id: int = Field(..., description="ID of the team to join")
    message: Optional[str] = Field(None, max_length=500, description="Message to the team captain")
    position: Optional[str] = Field(None, max_length=50, description="Preferred playing position")


class JoinRequestReview(BaseModel):
    """Schema for captain reviewing a join request"""
    status: JoinRequestStatus = Field(..., description="New status (ACCEPTED or REJECTED)")
    review_message: Optional[str] = Field(None, max_length=500, description="Response message to the player")


class JoinRequestUserInfo(BaseModel):
    """Basic user info for join request"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class JoinRequestTeamInfo(BaseModel):
    """Basic team info for join request"""
    id: int
    name: str
    city: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


class JoinRequestResponse(BaseModel):
    """Schema for join request response"""
    id: int
    team_id: int
    user_id: int
    status: JoinRequestStatus
    message: Optional[str] = None
    position: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user: JoinRequestUserInfo
    team: JoinRequestTeamInfo

    class Config:
        from_attributes = True


class JoinRequestListResponse(BaseModel):
    """Paginated list of join requests"""
    items: list[JoinRequestResponse]
    total: int
    skip: int
    limit: int


class MyJoinRequestResponse(BaseModel):
    """Schema for player viewing their own join requests"""
    id: int
    team_id: int
    status: JoinRequestStatus
    message: Optional[str] = None
    position: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_message: Optional[str] = None
    created_at: datetime
    team: JoinRequestTeamInfo

    class Config:
        from_attributes = True
