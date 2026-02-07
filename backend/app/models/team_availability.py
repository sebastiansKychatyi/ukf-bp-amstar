from sqlalchemy import Column, Integer, String, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class TeamAvailability(Base):
    """
    Represents a team's recurring weekly availability window.

    Each row is one time slot on a specific day of the week.
    A team can have multiple slots (e.g., Monday 18:00-20:00 and Wednesday 19:00-21:00).
    """

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday .. 6=Sunday (ISO 8601)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location_preference = Column(String(200), nullable=True)

    # Prevent duplicate slots for the same team/day/time
    __table_args__ = (
        UniqueConstraint("team_id", "day_of_week", "start_time", name="uq_team_day_start"),
    )

    # Relationships
    team = relationship("Team", back_populates="availability_slots")
