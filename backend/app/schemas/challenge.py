"""
Challenge Schemas

Pydantic schemas for the Challenge / Battle system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Импортируем Python-enum отсюда, чтобы:
# 1. ChallengeResponse.status имел правильный тип (не просто str)
# 2. FastAPI мог автоматически валидировать значения query-параметра ?status=
# 3. OpenAPI schema показывала допустимые значения
from app.models.challenge import ChallengeStatus


class ChallengeCreate(BaseModel):
    """Schema for creating a new challenge (Captain → Opponent)."""
    opponent_id: int = Field(..., gt=0, description="ID of the team being challenged")
    match_date: Optional[datetime] = Field(None, description="Proposed match date/time (ISO 8601)")
    location: Optional[str] = Field(None, max_length=200, description="Proposed match venue")
    # message хранится в схеме для будущего использования (сейчас ignored в сервисе)
    message: Optional[str] = Field(None, max_length=500, description="Optional message to opponent")


class ChallengeResultSubmit(BaseModel):
    """Schema for recording match result after the game."""
    challenger_score: int = Field(..., ge=0, le=99, description="Goals scored by challenger")
    opponent_score: int = Field(..., ge=0, le=99, description="Goals scored by opponent")


class TeamBrief(BaseModel):
    """Minimal team info embedded in challenge responses."""
    id: int
    name: str
    city: Optional[str] = None
    rating: Optional[int] = 1000

    class Config:
        from_attributes = True


class ChallengeResponse(BaseModel):
    """Full challenge response with team details."""
    id: int
    challenger_id: int
    opponent_id: int
    # ChallengeStatus вместо str — три преимущества:
    # 1. Pydantic валидирует при создании response (отловит несоответствие DB↔enum)
    # 2. OpenAPI schema показывает enum values в Swagger UI
    # 3. use_enum_values=True гарантирует, что клиент получает строку 'pending',
    #    а не Python repr 'ChallengeStatus.PENDING'
    status: ChallengeStatus
    match_date: Optional[datetime] = None
    location: Optional[str] = None
    challenger_score: Optional[int] = None
    opponent_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Nested team info (populated via joinedload)
    challenger: Optional[TeamBrief] = None
    opponent: Optional[TeamBrief] = None

    class Config:
        from_attributes = True
        # Сериализуем enum как его .value ('pending'), не как Python объект.
        # Без этого Pydantic v1 мог бы вернуть строку 'ChallengeStatus.PENDING'.
        # В Pydantic v2 + str-enum это лишний страховочный пояс.
        use_enum_values = True


class ChallengeListResponse(BaseModel):
    """Paginated list of challenges."""
    items: List[ChallengeResponse]
    total: int
    skip: int
    limit: int


class EloUpdateResult(BaseModel):
    """Result of ELO recalculation after a match."""
    team_id: int
    team_name: str
    old_rating: int
    new_rating: int
    rating_change: int


class ChallengeCompleteResponse(BaseModel):
    """Response after completing a challenge (scores + ELO updates)."""
    challenge: ChallengeResponse
    elo_updates: List[EloUpdateResult]
