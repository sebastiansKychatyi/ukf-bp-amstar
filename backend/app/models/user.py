from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.db.base_class import Base


class UserRole(str, PyEnum):
    """
    User roles in the system:
    - PLAYER: Can join teams and participate in matches
    - CAPTAIN: Can create/manage a team, invite players, and challenge other teams
    - REFEREE: Can verify match results and edit match statistics
    """
    PLAYER = "PLAYER"
    CAPTAIN = "CAPTAIN"
    REFEREE = "REFEREE"


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.PLAYER)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    captained_team = relationship("Team", back_populates="captain", uselist=False, foreign_keys="Team.captain_id")

    # Team membership (player can be in one team)
    team_membership = relationship("TeamMember", back_populates="user", uselist=False)
    join_requests_sent = relationship("JoinRequest", foreign_keys="JoinRequest.user_id", back_populates="user")
    statistics = relationship("PlayerStatistics", back_populates="user", uselist=False)
