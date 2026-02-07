"""Add matchmaking tables and geo fields

Revision ID: a1b2c3d4e5f6
Revises: df7e4f8587b7
Create Date: 2026-02-07 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'df7e4f8587b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add geographic coordinates to team table
    op.add_column('team', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('team', sa.Column('longitude', sa.Float(), nullable=True))

    # Create team availability table
    op.create_table(
        'teamavailability',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('location_preference', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['team.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_id', 'day_of_week', 'start_time', name='uq_team_day_start'),
    )
    op.create_index(
        op.f('ix_teamavailability_id'), 'teamavailability', ['id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_teamavailability_id'), table_name='teamavailability')
    op.drop_table('teamavailability')
    op.drop_column('team', 'longitude')
    op.drop_column('team', 'latitude')
