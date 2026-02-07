from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class Team(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    captain_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    city = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    founded_date = Column(DateTime)
    logo_url = Column(String)
    rating = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (lazy loading to avoid circular import issues)
    captain = relationship("User", back_populates="captained_team", foreign_keys=[captain_id])
    challenges_sent = relationship("Challenge", foreign_keys="Challenge.challenger_id", back_populates="challenger", lazy="select")
    challenges_received = relationship("Challenge", foreign_keys="Challenge.opponent_id", back_populates="opponent", lazy="select")
    availability_slots = relationship("TeamAvailability", back_populates="team", cascade="all, delete-orphan")

    # Team members (many-to-many via TeamMember)
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    join_requests = relationship("JoinRequest", back_populates="team", cascade="all, delete-orphan")

    @property
    def member_count(self) -> int:
        """Number of team members (available when members are loaded)."""
        if self.members is not None:
            return len(self.members)
        return 0

    @property
    def rating_score(self) -> int:
        """Alias for rating to match schema field name."""
        return self.rating or 1000

    @property
    def founded_year(self):
        """Extract year from founded_date for schema compatibility."""
        if self.founded_date:
            return self.founded_date.year
        return None
