"""Fix challengestatus enum values: UPPERCASE → lowercase

The initial migration created the PostgreSQL enum type from Python enum member
names ('PENDING', 'ACCEPTED', ...) instead of their values. The model uses
values_callable so the application writes lowercase values ('pending', ...) to
the DB, causing a DataError on every insert.

ALTER TYPE ... RENAME VALUE is transactional in PostgreSQL 10+ and runs inside
Alembic's managed transaction — no manual COMMIT required.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-19 00:00:00.000000
"""

from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'PENDING'   TO 'pending'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'ACCEPTED'  TO 'accepted'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'REJECTED'  TO 'rejected'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'COMPLETED' TO 'completed'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'CANCELLED' TO 'cancelled'")


def downgrade() -> None:
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'pending'   TO 'PENDING'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'accepted'  TO 'ACCEPTED'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'rejected'  TO 'REJECTED'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'completed' TO 'COMPLETED'")
    op.execute("ALTER TYPE challengestatus RENAME VALUE 'cancelled' TO 'CANCELLED'")
