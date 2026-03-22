"""add result_confirmed_by_challenger and result_confirmed_by_opponent to challenge

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-22 01:00:00.000000

Adds two Boolean columns that implement the two-captain result-confirmation
workflow described in the ER diagram (Obrázok 2) of the thesis.  A challenge
transitions to COMPLETED only after both captains have set their flag to True.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "challenge",
        sa.Column(
            "result_confirmed_by_challenger",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "challenge",
        sa.Column(
            "result_confirmed_by_opponent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("challenge", "result_confirmed_by_opponent")
    op.drop_column("challenge", "result_confirmed_by_challenger")
