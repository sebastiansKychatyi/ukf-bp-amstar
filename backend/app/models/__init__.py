"""
SQLAlchemy models for the AmStar Football Platform
"""

from app.models.user import User, UserRole
from app.models.team import Team
from app.models.challenge import Challenge
from app.models.rating import Rating

__all__ = [
    "User",
    "UserRole",
    "Team",
    "Challenge",
    "Rating",
]
