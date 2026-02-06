from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TeamBase(BaseModel):
    """Base Team schema with common attributes"""
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    city: Optional[str] = Field(None, max_length=100, description="Team city")
    rating_score: int = Field(default=1000, ge=0, le=5000, description="Team rating score")


class TeamCreate(TeamBase):
    """Schema for creating a new team"""
    description: Optional[str] = Field(None, description="Team description")
    founded_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year the team was founded")


class TeamUpdate(BaseModel):
    """Schema for updating an existing team"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    rating_score: Optional[int] = Field(None, ge=0, le=5000)


class CaptainInfo(BaseModel):
    """Basic captain info for team response"""
    id: int
    username: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class TeamResponse(TeamBase):
    """Schema for team response with all fields"""
    id: int
    captain_id: int
    description: Optional[str] = None
    founded_year: Optional[int] = None
    logo_url: Optional[str] = None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TeamWithCaptain(TeamResponse):
    """Team response including captain details"""
    captain: Optional[CaptainInfo] = None

    class Config:
        from_attributes = True


class Team(TeamResponse):
    """Complete Team model for API responses"""
    pass


class TeamDetailResponse(TeamResponse):
    """Detailed team response with captain info for team detail page"""
    captain: Optional[CaptainInfo] = None

    class Config:
        from_attributes = True


class MatchHistoryItem(BaseModel):
    """Single match history entry"""
    challenge_id: int
    opponent_id: int
    opponent_name: str
    match_date: Optional[datetime] = None
    location: Optional[str] = None
    team_score: Optional[int] = None
    opponent_score: Optional[int] = None
    result: Optional[str] = None  # "W", "L", "D"
    status: str

    class Config:
        from_attributes = True


class TeamStatsSummary(BaseModel):
    """Aggregated team statistics"""
    total_matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    goal_difference: int = 0
    win_rate: float = 0.0
