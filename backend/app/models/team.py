from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


class Team(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    captain_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    city = Column(String)
    founded_date = Column(DateTime)
    logo_url = Column(String)
    rating = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (lazy loading to avoid circular import issues)
    captain = relationship("User", back_populates="captained_team", foreign_keys=[captain_id])
    challenges_sent = relationship("Challenge", foreign_keys="Challenge.challenger_id", back_populates="challenger", lazy="select")
    challenges_received = relationship("Challenge", foreign_keys="Challenge.opponent_id", back_populates="opponent", lazy="select")
