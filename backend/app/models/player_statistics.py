"""
Player Statistics Model

Tracks individual player performance metrics including:
- Goals, assists, and other offensive stats
- Cards (yellow, red)
- Match participation
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base_class import Base


class PlayerStatistics(Base):
    """
    Aggregated player statistics

    This model stores cumulative statistics for each player.
    Can be updated after each match or recalculated from match data.
    """
    __tablename__ = "playerstatistics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Match statistics
    matches_played = Column(Integer, default=0)
    matches_won = Column(Integer, default=0)
    matches_drawn = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)

    # Offensive statistics
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)

    # Disciplinary statistics
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)

    # Goalkeeper statistics (optional)
    clean_sheets = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="statistics")


class MatchPlayerStatistics(Base):
    """
    Per-match player statistics

    Records individual player performance in each match.
    Used to calculate aggregated PlayerStatistics.
    """
    __tablename__ = "matchplayerstatistics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenge.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("team.id", ondelete="CASCADE"), nullable=False)

    # Match performance
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    minutes_played = Column(Integer, default=0)

    # Additional stats
    shots_on_target = Column(Integer, default=0)
    saves = Column(Integer, default=0)  # For goalkeepers

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User")
    challenge = relationship("Challenge")
    team = relationship("Team")
