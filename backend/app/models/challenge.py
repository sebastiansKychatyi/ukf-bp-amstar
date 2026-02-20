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

    @classmethod
    def _missing_(cls, value: object) -> "ChallengeStatus | None":
        """
        Fallback для значений, не найденных в _value2member_map_.

        Python вызывает _missing_ автоматически из Enum.__new__, когда
        ChallengeStatus('COMPLETED') не находит 'COMPLETED' в карте значений.

        Нормализуем к lowercase и ищем снова — это позволяет SQLAlchemy
        прочитать любые legacy-записи с UPPERCASE статусами без LookupError.

        Почему нужно даже после миграции:
        - Защита от ручного INSERT/UPDATE в обход приложения
        - Защита от data migration из внешних источников
        - Страховка при будущих изменениях схемы
        """
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
            native_enum=False,      # Store as VARCHAR(20) — no PostgreSQL ENUM type
            create_constraint=False,  # Python enum already validates; skip DB CHECK
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    challenger = relationship("Team", foreign_keys=[challenger_id], back_populates="challenges_sent")
    opponent = relationship("Team", foreign_keys=[opponent_id], back_populates="challenges_received")
