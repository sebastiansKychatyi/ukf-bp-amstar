"""
Player Statistics Schemas

Pydantic schemas for player statistics operations.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class PlayerStatisticsBase(BaseModel):
    """Base schema for player statistics"""
    matches_played: int = Field(default=0, ge=0)
    matches_won: int = Field(default=0, ge=0)
    matches_drawn: int = Field(default=0, ge=0)
    matches_lost: int = Field(default=0, ge=0)
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    shots_on_target: int = Field(default=0, ge=0)
    yellow_cards: int = Field(default=0, ge=0)
    red_cards: int = Field(default=0, ge=0)
    clean_sheets: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)


class PlayerStatisticsCreate(PlayerStatisticsBase):
    """Schema for creating player statistics"""
    user_id: int


class PlayerStatisticsUpdate(BaseModel):
    """Schema for updating player statistics"""
    matches_played: Optional[int] = Field(None, ge=0)
    matches_won: Optional[int] = Field(None, ge=0)
    matches_drawn: Optional[int] = Field(None, ge=0)
    matches_lost: Optional[int] = Field(None, ge=0)
    goals: Optional[int] = Field(None, ge=0)
    assists: Optional[int] = Field(None, ge=0)
    shots_on_target: Optional[int] = Field(None, ge=0)
    yellow_cards: Optional[int] = Field(None, ge=0)
    red_cards: Optional[int] = Field(None, ge=0)
    clean_sheets: Optional[int] = Field(None, ge=0)
    saves: Optional[int] = Field(None, ge=0)


class PlayerStatisticsResponse(PlayerStatisticsBase):
    """Schema for player statistics response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchPlayerStatisticsCreate(BaseModel):
    """Schema for recording per-match player statistics"""
    user_id: int
    challenge_id: int
    team_id: int
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    yellow_cards: int = Field(default=0, ge=0)
    red_cards: int = Field(default=0, ge=0)
    minutes_played: int = Field(default=0, ge=0, le=120)
    shots_on_target: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)


class MatchPlayerStatisticsResponse(MatchPlayerStatisticsCreate):
    """Schema for per-match statistics response"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlayerProfileWithStats(BaseModel):
    """Complete player profile with statistics and team info"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: str
    team_name: Optional[str] = None
    team_id: Optional[int] = None
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    statistics: Optional[PlayerStatisticsResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TeamStatisticsResponse(BaseModel):
    """Aggregated team statistics"""
    team_id: int
    team_name: str
    total_matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    goal_difference: int = 0
    points: int = 0  # 3 for win, 1 for draw
    rating: int = 1000
