"""add unique constraint joinrequest user_team

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-04-12 01:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_joinrequest_user_team",
        "joinrequest",
        ["user_id", "team_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_joinrequest_user_team",
        "joinrequest",
        type_="unique",
    )
