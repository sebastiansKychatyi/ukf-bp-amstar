"""add tournament tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-12 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tournament type and status enums
    tournament_type = sa.Enum("league", "knockout", name="tournamenttype")
    tournament_status = sa.Enum(
        "draft", "registration", "active", "completed", "cancelled",
        name="tournamentstatus",
    )

    # Tournament table
    op.create_table(
        "tournament",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", tournament_type, nullable=False, server_default="league"),
        sa.Column("status", tournament_status, nullable=False, server_default="draft"),
        sa.Column("max_teams", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("current_round", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_by_id",
            sa.Integer(),
            sa.ForeignKey("user.id"),
            nullable=False,
        ),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint("max_teams >= 2", name="ck_tournament_min_teams"),
    )

    # TournamentParticipant table
    op.create_table(
        "tournamentparticipant",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tournament_id",
            sa.Integer(),
            sa.ForeignKey("tournament.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("team.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("is_eliminated", sa.Integer(), nullable=False, server_default="0"),
        # Denormalised standings
        sa.Column("played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("draws", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals_for", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("goals_against", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("tournament_id", "team_id", name="uq_tournament_team"),
    )
    op.create_index(
        "ix_tournamentparticipant_tournament",
        "tournamentparticipant",
        ["tournament_id"],
    )

    # TournamentMatch table
    op.create_table(
        "tournamentmatch",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tournament_id",
            sa.Integer(),
            sa.ForeignKey("tournament.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "challenge_id",
            sa.Integer(),
            sa.ForeignKey("challenge.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
        ),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("match_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "home_team_id",
            sa.Integer(),
            sa.ForeignKey("team.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "away_team_id",
            sa.Integer(),
            sa.ForeignKey("team.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "winner_team_id",
            sa.Integer(),
            sa.ForeignKey("team.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint(
            "home_team_id != away_team_id",
            name="ck_tournamentmatch_different_teams",
        ),
    )

    # Extend notification enum with tournament events
    # PostgreSQL requires ALTER TYPE to add values to an existing enum
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'tournament_started'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'tournament_match_scheduled'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'tournament_completed'")


def downgrade() -> None:
    op.drop_table("tournamentmatch")
    op.drop_table("tournamentparticipant")
    op.drop_table("tournament")
    op.execute("DROP TYPE IF EXISTS tournamenttype")
    op.execute("DROP TYPE IF EXISTS tournamentstatus")
    # Note: PostgreSQL does not support removing individual values from an enum.
    # The three tournament notification values will remain in notificationtype.
