from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.db.base_class import Base


class ChallengeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def _missing_(cls, value: object) -> "ChallengeStatus | None":
        """Normalise legacy uppercase values stored in the database."""
        if isinstance(value, str):
            normalized = value.lower()
            for member in cls:
                if member.value == normalized:
                    return member
        return None


class Challenge(Base):
    id = Column(Integer, primary_key=True, index=True)
    challenger_id = Column(Integer, ForeignKey("team.id"), nullable=False)
    opponent_id = Column(Integer, ForeignKey("team.id"), nullable=False)
    status = Column(
        SQLEnum(
            ChallengeStatus,
            name="challengestatus",
            native_enum=False,
            create_constraint=False,
            length=20,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ChallengeStatus.PENDING,
        nullable=True,
    )
    match_date = Column(DateTime)
    location = Column(String)
    challenger_score = Column(Integer)
    opponent_score = Column(Integer)
    result_confirmed_by_challenger = Column(Boolean, default=False, nullable=False)
    result_confirmed_by_opponent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    challenger = relationship("Team", foreign_keys=[challenger_id], back_populates="challenges_sent")
    opponent = relationship("Team", foreign_keys=[opponent_id], back_populates="challenges_received")
