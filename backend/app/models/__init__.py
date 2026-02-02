"""
SQLAlchemy models for the AmStar Football Platform
"""

from app.models.user import User, UserRole
from app.models.team import Team
from app.models.challenge import Challenge
from app.models.rating import Rating
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.join_request import JoinRequest, JoinRequestStatus
from app.models.player_statistics import PlayerStatistics, MatchPlayerStatistics

__all__ = [
    "User",
    "UserRole",
    "Team",
    "Challenge",
    "Rating",
    "TeamMember",
    "TeamMemberRole",
    "JoinRequest",
    "JoinRequestStatus",
    "PlayerStatistics",
    "MatchPlayerStatistics",
]
