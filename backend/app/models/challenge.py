from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base_class import Base


class ChallengeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Challenge(Base):
    id = Column(Integer, primary_key=True, index=True)
    challenger_id = Column(Integer, ForeignKey("team.id"), nullable=False)
    opponent_id = Column(Integer, ForeignKey("team.id"), nullable=False)
    status = Column(
        SQLEnum(ChallengeStatus, values_callable=lambda x: [e.value for e in x]),
        default=ChallengeStatus.PENDING,
    )
    match_date = Column(DateTime)
    location = Column(String)
    challenger_score = Column(Integer)
    opponent_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    challenger = relationship("Team", foreign_keys=[challenger_id], back_populates="challenges_sent")
    opponent = relationship("Team", foreign_keys=[opponent_id], back_populates="challenges_received")
