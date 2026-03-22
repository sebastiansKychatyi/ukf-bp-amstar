"""Pydantic schemas for the Challenge system."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

from app.models.challenge import ChallengeStatus


class ChallengeCreate(BaseModel):
    """Schema for creating a new challenge."""
    opponent_id: int = Field(..., gt=0, description="ID of the team being challenged")
    match_date: Optional[datetime] = Field(None, description="Proposed match date/time (ISO 8601)")
    location: Optional[str] = Field(None, max_length=200, description="Proposed match venue")
    message: Optional[str] = Field(None, max_length=500, description="Optional message to opponent")


class ChallengeResultSubmit(BaseModel):
    """Schema for recording match result."""
    challenger_score: int = Field(..., ge=0, le=99, description="Goals scored by challenger")
    opponent_score: int = Field(..., ge=0, le=99, description="Goals scored by opponent")


class TeamBrief(BaseModel):
    """Minimal team info embedded in challenge responses."""
    id: int
    name: str
    city: Optional[str] = None
    rating: Optional[int] = 1000

    model_config = ConfigDict(from_attributes=True)


class ChallengeResponse(BaseModel):
    """Full challenge response with team details."""
    id: int
    challenger_id: int
    opponent_id: int
    status: ChallengeStatus
    match_date: Optional[datetime] = None
    location: Optional[str] = None
    challenger_score: Optional[int] = None
    opponent_score: Optional[int] = None
    result_confirmed_by_challenger: bool = False
    result_confirmed_by_opponent: bool = False
    created_at: datetime
    updated_at: datetime
    challenger: Optional[TeamBrief] = None
    opponent: Optional[TeamBrief] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ChallengeListResponse(BaseModel):
    """Paginated list of challenges."""
    items: List[ChallengeResponse]
    total: int
    skip: int
    limit: int


class EloUpdateResult(BaseModel):
    """ELO rating change for one team after a match."""
    team_id: int
    team_name: str
    old_rating: int
    new_rating: int
    rating_change: int


class ChallengeCompleteResponse(BaseModel):
    """Response after completing a challenge (scores + ELO updates)."""
    challenge: ChallengeResponse
    elo_updates: List[EloUpdateResult]
