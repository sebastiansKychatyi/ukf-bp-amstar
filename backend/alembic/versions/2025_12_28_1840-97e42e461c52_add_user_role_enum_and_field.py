"""add_user_role_enum_and_field

Revision ID: 97e42e461c52
Revises: 62f47e93a625
Create Date: 2025-12-28 18:40:29.545954

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '97e42e461c52'
down_revision = '62f47e93a625'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the UserRole enum type in PostgreSQL
    user_role_enum = postgresql.ENUM('PLAYER', 'CAPTAIN', 'REFEREE', name='userrole')
    user_role_enum.create(op.get_bind())

    # Add role column to user table with default value 'PLAYER'
    op.add_column('user', sa.Column('role', sa.Enum('PLAYER', 'CAPTAIN', 'REFEREE', name='userrole'), nullable=False, server_default='PLAYER'))

    # Create index on role column for faster queries
    op.create_index(op.f('ix_user_role'), 'user', ['role'], unique=False)

    # Note: captain_id in team table is already NOT NULL from previous migration
    # If it wasn't, we would add: op.alter_column('team', 'captain_id', nullable=False)


def downgrade() -> None:
    # Drop the index
    op.drop_index(op.f('ix_user_role'), table_name='user')

    # Drop the role column
    op.drop_column('user', 'role')

    # Drop the UserRole enum type
    user_role_enum = postgresql.ENUM('PLAYER', 'CAPTAIN', 'REFEREE', name='userrole')
    user_role_enum.drop(op.get_bind())
