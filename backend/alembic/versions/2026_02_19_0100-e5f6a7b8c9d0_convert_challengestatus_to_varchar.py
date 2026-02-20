"""Convert challengestatus column from PG ENUM to VARCHAR(20)

Permanently eliminates the native PostgreSQL ENUM type for challenge.status,
replacing it with a plain VARCHAR(20). This removes all case-sensitivity issues
and makes the column immune to future enum-value migration problems.

Background
----------
The original migration (62f47e93a625) created the PG enum with member NAMES
('PENDING', 'ACCEPTED', ...) instead of VALUES ('pending', 'accepted', ...).
Migration d4e5f6a7b8c9 attempted to RENAME the values to lowercase but was
never applied. This migration supersedes it and fixes the DB regardless of
whether the emergency docker exec fix was already run.

Design
------
• Idempotent: safe to run even if the column is already VARCHAR (e.g. after
  the emergency docker exec fix — the ALTER block is skipped via IF EXISTS).
• Normalizes any residual UPPERCASE rows to lowercase after converting.
• Drops the PG type with IF EXISTS so it never raises if already gone.

Revision ID: e5f6a7b8c9d0
Revises:     d4e5f6a7b8c9
Create Date: 2026-02-19 01:00:00.000000
"""

from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Convert to VARCHAR only if still a native enum.
    # information_schema.columns reports enum columns as data_type = 'USER-DEFINED'.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name  = 'challenge'
                  AND column_name = 'status'
                  AND data_type   = 'USER-DEFINED'
            ) THEN
                ALTER TABLE challenge
                    ALTER COLUMN status TYPE VARCHAR(20) USING status::text;
            END IF;
        END $$
    """)

    # Step 2: Normalize any UPPERCASE values that survived.
    op.execute("""
        UPDATE challenge
           SET status = lower(status)
         WHERE status IS NOT NULL
           AND status != lower(status)
    """)

    # Step 3: Remove the now-unused PG enum type.
    op.execute("DROP TYPE IF EXISTS challengestatus")


def downgrade() -> None:
    # Recreate the enum (lowercase values) and restore the column type.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'challengestatus'
            ) THEN
                CREATE TYPE challengestatus AS ENUM
                    ('pending', 'accepted', 'rejected', 'completed', 'cancelled');
            END IF;
        END $$
    """)
    op.execute("""
        ALTER TABLE challenge
            ALTER COLUMN status
            TYPE challengestatus
            USING status::challengestatus
    """)
