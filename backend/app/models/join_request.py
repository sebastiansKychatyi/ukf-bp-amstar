"""
Join Request Model

Represents player requests to join teams.
Managed by team captains who can accept or reject requests.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum
from app.db.base_class import Base


class JoinRequestStatus(str, PyEnum):
    """
    Status of a join request:
    - PENDING: Awaiting captain's review
    - ACCEPTED: Request accepted, player joined team
    - REJECTED: Request rejected by captain
    - CANCELLED: Request cancelled by player
    - EXPIRED: Request expired (optional timeout)
    """
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class JoinRequest(Base):
    """
    Model for tracking player join requests to teams

    Workflow:
    1. Player submits request to join a team
    2. Team captain reviews pending requests
    3. Captain accepts/rejects request
    4. If accepted, player is added to team as TeamMember
    """
    __tablename__ = "joinrequest"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(JoinRequestStatus), nullable=False, default=JoinRequestStatus.PENDING)

    # Request details
    message = Column(Text)  # Player's message to captain
    position = Column(String(50))  # Preferred position

    # Review details
    reviewed_by_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    reviewed_at = Column(DateTime)
    review_message = Column(Text)  # Captain's response message

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    team = relationship("Team", back_populates="join_requests")
    user = relationship("User", foreign_keys=[user_id], back_populates="join_requests_sent")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
