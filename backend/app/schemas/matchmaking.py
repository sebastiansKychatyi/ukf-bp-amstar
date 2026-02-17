from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import time


# ============================================================================
# TEAM AVAILABILITY SCHEMAS
# ============================================================================


class AvailabilitySlotBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday .. 6=Sunday (ISO 8601)")
    start_time: time = Field(..., description="Slot start time (HH:MM)")
    end_time: time = Field(..., description="Slot end time (HH:MM)")
    location_preference: Optional[str] = Field(None, max_length=200)


class AvailabilitySlotCreate(AvailabilitySlotBase):
    pass


class AvailabilitySlotResponse(AvailabilitySlotBase):
    id: int
    team_id: int

    class Config:
        from_attributes = True


class TeamAvailabilityUpdate(BaseModel):
    """Replace all availability slots for a team at once."""
    slots: List[AvailabilitySlotCreate] = Field(
        ..., max_length=21, description="Up to 3 slots per day x 7 days"
    )


class TeamAvailabilityResponse(BaseModel):
    team_id: int
    team_name: str
    slots: List[AvailabilitySlotResponse]


# ============================================================================
# MATCHMAKING SCHEMAS
# ============================================================================


class MatchmakingScoreBreakdown(BaseModel):
    """Detailed breakdown of how the match score was calculated."""
    elo_similarity: float = Field(..., description="Score from ELO proximity (0-1)")
    geo_proximity: float = Field(..., description="Score from geographic distance (0-1)")
    availability_overlap: float = Field(..., description="Score from schedule overlap (0-1)")
    recency_penalty: float = Field(..., description="Penalty for recent matches (0-1)")
    activity_bonus: float = Field(..., description="Bonus for active teams (0-1)")


class MatchmakingSuggestion(BaseModel):
    """A single opponent suggestion with score and details."""
    team_id: int
    team_name: str
    city: Optional[str] = None
    rating: int
    rating_difference: int
    member_count: int
    total_score: float = Field(..., description="Composite matchmaking score (0-100)")
    breakdown: MatchmakingScoreBreakdown
    overlapping_slots: int = Field(0, description="Number of matching time windows")
    distance_km: Optional[float] = Field(
        None,
        description="Great-circle distance in km (only present when both teams have coordinates)",
    )


class MatchmakingResponse(BaseModel):
    """Response from the matchmaking endpoint."""
    requesting_team_id: int
    requesting_team_rating: int
    suggestions: List[MatchmakingSuggestion]
    total_candidates: int = Field(..., description="Teams evaluated before ranking")


class MatchmakingConfig(BaseModel):
    """Optional overrides for matchmaking weights (for experimentation)."""
    w_elo: float = Field(0.35, ge=0, le=1, description="Weight for ELO similarity")
    w_geo: float = Field(0.25, ge=0, le=1, description="Weight for geographic proximity")
    w_avail: float = Field(0.20, ge=0, le=1, description="Weight for availability overlap")
    w_recency: float = Field(0.10, ge=0, le=1, description="Weight for recency penalty")
    w_activity: float = Field(0.10, ge=0, le=1, description="Weight for activity bonus")
    max_results: int = Field(10, ge=1, le=50, description="Maximum suggestions returned")
    elo_range: int = Field(500, ge=50, le=2000, description="Maximum ELO difference to consider")
