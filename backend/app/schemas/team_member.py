"""
Team Member Schemas

Pydantic schemas for team membership operations.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TeamMemberRole(str, Enum):
    """Role within a team"""
    CAPTAIN = "CAPTAIN"
    PLAYER = "PLAYER"


class TeamMemberBase(BaseModel):
    """Base schema for team member"""
    position: Optional[str] = Field(None, max_length=50, description="Playing position (GK, DEF, MID, FWD)")
    jersey_number: Optional[int] = Field(None, ge=1, le=99, description="Jersey number")


class TeamMemberCreate(TeamMemberBase):
    """Schema for adding a member to a team (used internally after join request approval)"""
    user_id: int
    team_id: int
    role: TeamMemberRole = TeamMemberRole.PLAYER


class TeamMemberUpdate(BaseModel):
    """Schema for updating team member info"""
    position: Optional[str] = Field(None, max_length=50)
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    role: Optional[TeamMemberRole] = None


class TeamMemberUserInfo(BaseModel):
    """Basic user info for team member response"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: str

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(TeamMemberBase):
    """Schema for team member response"""
    id: int
    team_id: int
    user_id: int
    role: TeamMemberRole
    joined_at: datetime
    user: TeamMemberUserInfo

    model_config = ConfigDict(from_attributes=True)


class TeamMemberWithStats(TeamMemberResponse):
    """Team member with statistics"""
    goals: int = 0
    assists: int = 0
    matches_played: int = 0
    yellow_cards: int = 0
    red_cards: int = 0


class TeamRoster(BaseModel):
    """Complete team roster"""
    team_id: int
    team_name: str
    captain: Optional[TeamMemberResponse] = None
    players: list[TeamMemberResponse] = []
    total_members: int = 0

    model_config = ConfigDict(from_attributes=True)
