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


class TeamResponse(TeamBase):
    """Schema for team response with all fields"""
    id: int
    description: Optional[str] = None
    founded_year: Optional[int] = None
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Team(TeamResponse):
    """Complete Team model for API responses"""
    pass
