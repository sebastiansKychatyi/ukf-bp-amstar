"""
Tournament Schemas

Pydantic schemas for tournament creation, management, standings, and responses.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class TournamentCreate(BaseModel):
    """Schema for creating a new tournament."""
    name: str = Field(..., min_length=1, max_length=200, description="Tournament name")
    description: Optional[str] = Field(None, description="Tournament description")
    type: str = Field("league", pattern="^(league|knockout)$", description="league or knockout")
    max_teams: int = Field(8, ge=2, le=64, description="Maximum number of teams")
    start_date: Optional[datetime] = Field(None, description="Planned start date")
    end_date: Optional[datetime] = Field(None, description="Planned end date")


class TournamentUpdate(BaseModel):
    """Schema for updating a tournament (only allowed in DRAFT/REGISTRATION)."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    max_teams: Optional[int] = Field(None, ge=2, le=64)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TournamentJoin(BaseModel):
    """Schema for a team joining a tournament."""
    team_id: int = Field(..., description="ID of the team to register")


class MatchResultSubmit(BaseModel):
    """Schema for submitting a tournament match result."""
    home_score: int = Field(..., ge=0, le=99, description="Goals scored by home team")
    away_score: int = Field(..., ge=0, le=99, description="Goals scored by away team")


# ---------------------------------------------------------------------------
# Response sub-schemas
# ---------------------------------------------------------------------------

class TeamBrief(BaseModel):
    """Minimal team info for embedding in tournament responses."""
    id: int
    name: str
    city: Optional[str] = None
    rating: int = 1000

    model_config = ConfigDict(from_attributes=True)


class ParticipantResponse(BaseModel):
    """A team's participation record within a tournament."""
    id: int
    tournament_id: int
    team_id: int
    seed: Optional[int] = None
    is_eliminated: int = 0
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    team: Optional[TeamBrief] = None

    model_config = ConfigDict(from_attributes=True)


class TournamentMatchResponse(BaseModel):
    """A single fixture in a tournament."""
    id: int
    tournament_id: int
    challenge_id: Optional[int] = None
    round_number: int
    match_order: int
    home_team_id: int
    away_team_id: Optional[int] = None
    winner_team_id: Optional[int] = None
    home_team: Optional[TeamBrief] = None
    away_team: Optional[TeamBrief] = None
    winner: Optional[TeamBrief] = None
    # Scores pulled from linked Challenge (if exists)
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Main tournament response
# ---------------------------------------------------------------------------

class CreatorBrief(BaseModel):
    """Brief info about the tournament organiser."""
    id: int
    username: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TournamentResponse(BaseModel):
    """Full tournament response."""
    id: int
    name: str
    description: Optional[str] = None
    type: str
    status: str
    max_teams: int
    current_round: int
    participant_count: int = 0
    created_by_id: int
    created_by: Optional[CreatorBrief] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TournamentListResponse(BaseModel):
    """Paginated list of tournaments."""
    items: List[TournamentResponse]
    total: int
    skip: int
    limit: int


class TournamentDetailResponse(TournamentResponse):
    """Tournament with full standings and bracket/fixtures."""
    participants: List[ParticipantResponse] = []
    matches: List[TournamentMatchResponse] = []

    model_config = ConfigDict(from_attributes=True)


class StandingsResponse(BaseModel):
    """League standings table (sorted by points, goal diff, goals for)."""
    tournament_id: int
    tournament_name: str
    standings: List[ParticipantResponse]


class BracketRound(BaseModel):
    """A single round in a knockout bracket."""
    round_number: int
    round_name: str   # e.g. "Quarter-finals", "Semi-finals", "Final"
    matches: List[TournamentMatchResponse]


class BracketResponse(BaseModel):
    """Full knockout bracket."""
    tournament_id: int
    tournament_name: str
    total_rounds: int
    rounds: List[BracketRound]


# ---------------------------------------------------------------------------
# Match result submission response (includes ELO updates)
# ---------------------------------------------------------------------------

class EloUpdateInfo(BaseModel):
    """ELO rating change for one team after a tournament match."""
    team_id: int
    team_name: str
    old_rating: int
    new_rating: int
    rating_change: int


class MatchResultResponse(TournamentMatchResponse):
    """
    Response from submitting a tournament match result.

    Extends the standard match response with optional ELO rating changes
    so the frontend can display "Home: +12 ELO · Away: -8 ELO" immediately
    after a result is submitted.
    """
    elo_home: Optional[EloUpdateInfo] = None
    elo_away: Optional[EloUpdateInfo] = None
