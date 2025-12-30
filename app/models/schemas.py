"""
Pydantic schemas for API request/response validation
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================

class PlayerPosition(str, Enum):
    """Player positions on the field"""
    GOALKEEPER = "GOALKEEPER"
    DEFENDER = "DEFENDER"
    MIDFIELDER = "MIDFIELDER"
    FORWARD = "FORWARD"


class PreferredFoot(str, Enum):
    """Player's preferred foot"""
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"


class TeamRole(str, Enum):
    """Role of a player within a team"""
    CAPTAIN = "CAPTAIN"
    MEMBER = "MEMBER"


class JoinRequestStatus(str, Enum):
    """Status of team join requests"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EventType(str, Enum):
    """Types of match events"""
    GOAL = "GOAL"
    ASSIST = "ASSIST"
    YELLOW_CARD = "YELLOW_CARD"
    RED_CARD = "RED_CARD"
    CLEAN_SHEET = "CLEAN_SHEET"


# ============================================================================
# PLAYER SCHEMAS
# ============================================================================

class PlayerBase(BaseModel):
    """Base player schema with common fields"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    date_of_birth: date
    phone: Optional[str] = Field(None, max_length=20)
    position: PlayerPosition
    preferred_foot: Optional[PreferredFoot] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None

    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Ensure player is at least 13 years old"""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13:
            raise ValueError('Player must be at least 13 years old')
        if age > 100:
            raise ValueError('Invalid date of birth')
        return v


class PlayerCreate(PlayerBase):
    """Schema for creating a new player"""
    user_id: UUID  # From authentication system


class PlayerUpdate(BaseModel):
    """Schema for updating player information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[PlayerPosition] = None
    preferred_foot: Optional[PreferredFoot] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None


class PlayerStatistics(BaseModel):
    """Player statistics data"""
    total_matches_played: int = 0
    total_goals: int = 0
    total_assists: int = 0
    total_yellow_cards: int = 0
    total_red_cards: int = 0
    total_clean_sheets: int = 0
    skill_rating: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)


class PlayerResponse(PlayerBase):
    """Complete player information response"""
    id: UUID
    user_id: UUID
    skill_rating: Decimal
    total_matches_played: int
    total_goals: int
    total_assists: int
    total_yellow_cards: int
    total_red_cards: int
    total_clean_sheets: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TEAM SCHEMAS
# ============================================================================

class TeamBase(BaseModel):
    """Base team schema with common fields"""
    name: str = Field(..., min_length=3, max_length=100)
    short_name: Optional[str] = Field(None, max_length=20)
    founded_date: Optional[date] = None
    home_city: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = None
    team_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    max_players: int = Field(default=25, ge=11, le=50)
    is_recruiting: bool = True
    description: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a new team"""
    captain_id: UUID  # Player ID who will be the captain


class TeamUpdate(BaseModel):
    """Schema for updating team information"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    short_name: Optional[str] = Field(None, max_length=20)
    founded_date: Optional[date] = None
    home_city: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = None
    team_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    max_players: Optional[int] = Field(None, ge=11, le=50)
    is_recruiting: Optional[bool] = None
    description: Optional[str] = None


class TeamStatistics(BaseModel):
    """Team performance statistics"""
    total_matches: int = 0
    total_wins: int = 0
    total_draws: int = 0
    total_losses: int = 0
    total_goals_scored: int = 0
    total_goals_conceded: int = 0
    team_rating: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)

    @property
    def win_rate(self) -> float:
        """Calculate win percentage"""
        if self.total_matches == 0:
            return 0.0
        return (self.total_wins / self.total_matches) * 100

    @property
    def goal_difference(self) -> int:
        """Calculate goal difference"""
        return self.total_goals_scored - self.total_goals_conceded


class TeamResponse(TeamBase):
    """Complete team information response"""
    id: UUID
    total_matches: int
    total_wins: int
    total_draws: int
    total_losses: int
    total_goals_scored: int
    total_goals_conceded: int
    team_rating: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TEAM MEMBER SCHEMAS
# ============================================================================

class TeamMemberBase(BaseModel):
    """Base schema for team membership"""
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    position_in_team: Optional[PlayerPosition] = None


class TeamMemberCreate(TeamMemberBase):
    """Schema for adding a player to a team"""
    team_id: UUID
    player_id: UUID
    role: TeamRole = TeamRole.MEMBER


class TeamMemberUpdate(BaseModel):
    """Schema for updating team member information"""
    jersey_number: Optional[int] = Field(None, ge=1, le=99)
    position_in_team: Optional[PlayerPosition] = None
    role: Optional[TeamRole] = None


class TeamMemberStats(BaseModel):
    """Team-specific statistics for a player"""
    matches_played: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    clean_sheets: int = 0


class TeamMemberResponse(TeamMemberBase):
    """Complete team member information"""
    id: UUID
    team_id: UUID
    player_id: UUID
    role: TeamRole
    matches_played: int
    goals: int
    assists: int
    yellow_cards: int
    red_cards: int
    clean_sheets: int
    joined_at: datetime
    left_at: Optional[datetime]
    is_active: bool

    # Nested player information
    player: Optional[PlayerResponse] = None

    class Config:
        from_attributes = True


# ============================================================================
# JOIN REQUEST SCHEMAS
# ============================================================================

class JoinRequestCreate(BaseModel):
    """Schema for creating a team join request"""
    team_id: UUID
    player_id: UUID
    message: Optional[str] = Field(None, max_length=500)


class JoinRequestReview(BaseModel):
    """Schema for reviewing a join request"""
    status: JoinRequestStatus = Field(..., description="APPROVED or REJECTED")
    review_message: Optional[str] = Field(None, max_length=500)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: JoinRequestStatus) -> JoinRequestStatus:
        """Ensure status is either APPROVED or REJECTED"""
        if v not in [JoinRequestStatus.APPROVED, JoinRequestStatus.REJECTED]:
            raise ValueError('Status must be APPROVED or REJECTED')
        return v


class JoinRequestResponse(BaseModel):
    """Complete join request information"""
    id: UUID
    team_id: UUID
    player_id: UUID
    status: JoinRequestStatus
    message: Optional[str]
    reviewed_by: Optional[UUID]
    review_message: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Nested information
    team: Optional[TeamResponse] = None
    player: Optional[PlayerResponse] = None

    class Config:
        from_attributes = True


# ============================================================================
# MATCH EVENT SCHEMAS
# ============================================================================

class MatchEventCreate(BaseModel):
    """Schema for creating a match event"""
    match_id: UUID
    team_id: UUID
    player_id: UUID
    event_type: EventType
    minute: Optional[int] = Field(None, ge=0, le=120)
    description: Optional[str] = None


class MatchEventResponse(BaseModel):
    """Complete match event information"""
    id: UUID
    match_id: UUID
    team_id: UUID
    player_id: UUID
    event_type: EventType
    minute: Optional[int]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BATCH UPDATE SCHEMAS
# ============================================================================

class PlayerStatsUpdate(BaseModel):
    """Schema for updating a player's statistics after a match"""
    player_id: UUID
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    yellow_cards: int = Field(default=0, ge=0, le=2)
    red_cards: int = Field(default=0, ge=0, le=1)
    clean_sheet: bool = False  # For goalkeepers

    @field_validator('yellow_cards', 'red_cards')
    @classmethod
    def validate_cards(cls, v: int, info) -> int:
        """Validate card counts"""
        if info.field_name == 'yellow_cards' and v > 2:
            raise ValueError('Maximum 2 yellow cards per match')
        if info.field_name == 'red_cards' and v > 1:
            raise ValueError('Maximum 1 red card per match')
        return v


class MatchStatsUpdate(BaseModel):
    """Schema for updating statistics for all players in a match"""
    match_id: UUID
    team_id: UUID
    player_stats: list[PlayerStatsUpdate]
    match_result: str = Field(..., pattern=r'^(WIN|DRAW|LOSS)$')
    goals_scored: int = Field(ge=0)
    goals_conceded: int = Field(ge=0)
