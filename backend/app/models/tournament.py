"""
Tournament Models

Supports two tournament formats:
- LEAGUE (round-robin): Every team plays every other team. Standings by points.
- KNOCKOUT (single-elimination): Bracket-style, losers eliminated each round.

Lifecycle:  DRAFT  ->  REGISTRATION  ->  ACTIVE  ->  COMPLETED  /  CANCELLED
            (setup)   (teams join)     (matches)    (finished)
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text,
    Enum as SQLEnum, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TournamentType(str, enum.Enum):
    LEAGUE = "league"          # Round-robin: all-vs-all
    KNOCKOUT = "knockout"      # Single-elimination bracket


class TournamentStatus(str, enum.Enum):
    DRAFT = "draft"            # Created, not yet open
    REGISTRATION = "registration"  # Teams can join
    ACTIVE = "active"          # Matches in progress
    COMPLETED = "completed"    # All matches finished
    CANCELLED = "cancelled"    # Cancelled by organiser


# ---------------------------------------------------------------------------
# Tournament
# ---------------------------------------------------------------------------

class Tournament(Base):
    """
    A tournament organised by a captain or referee.

    - ``max_teams``: upper limit of participating teams.
    - ``current_round``: tracks bracket progress in KNOCKOUT mode.
    """
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(
        SQLEnum(TournamentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TournamentType.LEAGUE,
    )
    status = Column(
        SQLEnum(TournamentStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TournamentStatus.DRAFT,
    )
    max_teams = Column(Integer, nullable=False, default=8)
    current_round = Column(Integer, nullable=False, default=0)

    # Who created / organises the tournament
    created_by_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    # Optional scheduling
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by = relationship("User", backref="tournaments_created")
    participants = relationship(
        "TournamentParticipant",
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentParticipant.seed",
    )
    matches = relationship(
        "TournamentMatch",
        back_populates="tournament",
        cascade="all, delete-orphan",
        order_by="TournamentMatch.round_number, TournamentMatch.match_order",
    )

    __table_args__ = (
        CheckConstraint("max_teams >= 2", name="ck_tournament_min_teams"),
    )

    @property
    def participant_count(self) -> int:
        if self.participants is not None:
            return len(self.participants)
        return 0


# ---------------------------------------------------------------------------
# TournamentParticipant
# ---------------------------------------------------------------------------

class TournamentParticipant(Base):
    """
    Links a Team to a Tournament.

    - ``seed``: seeding position (1 = top seed). Used for bracket placement.
    - ``is_eliminated``: set True in KNOCKOUT when the team loses.

    Standings fields (used mainly in LEAGUE):
    - points, wins, draws, losses, goals_for, goals_against
    These are denormalised for fast leaderboard queries and recalculated
    from TournamentMatch results whenever a match completes.
    """
    __tablename__ = "tournamentparticipant"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(
        Integer,
        ForeignKey("tournament.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id = Column(
        Integer,
        ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )
    seed = Column(Integer, nullable=True)
    is_eliminated = Column(Integer, nullable=False, default=0)  # 0/1 flag

    # Denormalised standings (recalculated from matches)
    played = Column(Integer, nullable=False, default=0)
    wins = Column(Integer, nullable=False, default=0)
    draws = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)
    goals_for = Column(Integer, nullable=False, default=0)
    goals_against = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tournament = relationship("Tournament", back_populates="participants")
    team = relationship("Team", backref="tournament_entries")

    __table_args__ = (
        UniqueConstraint("tournament_id", "team_id", name="uq_tournament_team"),
    )

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


# ---------------------------------------------------------------------------
# TournamentMatch
# ---------------------------------------------------------------------------

class TournamentMatch(Base):
    """
    Links an existing Challenge (match) to a tournament context.

    - ``round_number``: 1-based. In KNOCKOUT this is the bracket round
      (1 = round-of-16, 2 = quarter-final, …). In LEAGUE it groups
      fixtures into matchdays.
    - ``match_order``: ordering within the round (for bracket positioning).
    - ``challenge_id``: FK to the actual Challenge that holds scores.
      NULL until the match is scheduled / created.
    - ``home_team_id / away_team_id``: the two teams for this fixture.
      In KNOCKOUT, ``away_team_id`` can be NULL for a BYE.
    - ``winner_team_id``: set after the linked Challenge completes.
    """
    __tablename__ = "tournamentmatch"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(
        Integer,
        ForeignKey("tournament.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    challenge_id = Column(
        Integer,
        ForeignKey("challenge.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    round_number = Column(Integer, nullable=False)
    match_order = Column(Integer, nullable=False, default=1)

    home_team_id = Column(
        Integer,
        ForeignKey("team.id", ondelete="CASCADE"),
        nullable=False,
    )
    away_team_id = Column(
        Integer,
        ForeignKey("team.id", ondelete="CASCADE"),
        nullable=True,   # NULL = BYE in knockout
    )
    winner_team_id = Column(
        Integer,
        ForeignKey("team.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tournament = relationship("Tournament", back_populates="matches")
    challenge = relationship("Challenge", backref="tournament_match", uselist=False)
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    winner = relationship("Team", foreign_keys=[winner_team_id])

    __table_args__ = (
        CheckConstraint(
            "home_team_id != away_team_id",
            name="ck_tournamentmatch_different_teams",
        ),
    )
