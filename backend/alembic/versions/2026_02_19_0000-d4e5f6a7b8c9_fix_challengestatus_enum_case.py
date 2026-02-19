"""Fix challengestatus enum values: UPPERCASE → lowercase

Проблема: первая миграция (62f47e93a625) создала тип через autogenerate,
который взял имена членов Python enum ('PENDING', 'ACCEPTED', ...),
а не их значения. Модель challenge.py использует values_callable и отправляет
в БД строчные значения ('pending', 'completed', ...) — отсюда DataError.

Решение: ALTER TYPE ... RENAME VALUE — атомарная операция в PostgreSQL 10+,
выполняется внутри обычной транзакции (в отличие от ADD VALUE в PG < 12).
Никакого ручного COMMIT не нужно: Alembic управляет транзакцией сам.

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
    # ALTER TYPE ... RENAME VALUE транзакционна в PG 10+ (у нас PG 15).
    # Все пять переименований выполняются в одной транзакции Alembic —
    # при ошибке на любом шаге весь upgrade откатится автоматически.
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
