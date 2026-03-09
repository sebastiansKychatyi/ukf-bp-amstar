"""
Notification Model

Stores in-app notifications for users triggered by system events:
- Challenge received / accepted / rejected / completed
- Join request received / accepted / rejected
- ELO rating change after match
- Tournament events (started, match scheduled, completed)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.db.base_class import Base


class NotificationType(str, enum.Enum):
    # Challenge events
    CHALLENGE_RECEIVED = "challenge_received"
    CHALLENGE_ACCEPTED = "challenge_accepted"
    CHALLENGE_REJECTED = "challenge_rejected"
    CHALLENGE_CANCELLED = "challenge_cancelled"
    CHALLENGE_COMPLETED = "challenge_completed"

    # Join request events
    JOIN_REQUEST_RECEIVED = "join_request_received"
    JOIN_REQUEST_ACCEPTED = "join_request_accepted"
    JOIN_REQUEST_REJECTED = "join_request_rejected"

    # Rating events
    RATING_CHANGED = "rating_changed"

    # Tournament events
    TOURNAMENT_STARTED = "tournament_started"
    TOURNAMENT_MATCH_SCHEDULED = "tournament_match_scheduled"
    TOURNAMENT_COMPLETED = "tournament_completed"


class Notification(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    title = Column(String(200), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    related_id = Column(Integer, nullable=True)  # challenge_id, join_request_id, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="notifications")
