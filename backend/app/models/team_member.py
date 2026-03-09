"""
Team Member Model

Represents the many-to-many relationship between Users and Teams
with additional metadata like role, position, and join date.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum
from app.db.base_class import Base


class TeamMemberRole(str, PyEnum):
    """
    Roles within a team:
    - CAPTAIN: Team leader, can manage team and accept join requests
    - PLAYER: Regular team member
    """
    CAPTAIN = "CAPTAIN"
    PLAYER = "PLAYER"


class TeamMember(Base):
    """
    Association table for Team-User many-to-many relationship

    This model tracks:
    - Which users belong to which teams
    - Their role within the team (captain/player)
    - Their playing position
    - When they joined the team
    """
    __tablename__ = "teammember"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(TeamMemberRole), nullable=False, default=TeamMemberRole.PLAYER)
    position = Column(String(50))  # GK, DEF, MID, FWD, etc.
    jersey_number = Column(Integer)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Unique constraint: user can only be in one team
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_teammember_user'),
    )

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_membership")
