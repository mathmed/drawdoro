"""make soft-delete timestamps timezone-aware

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOFT_DELETE_TABLES = ("workspaces", "projects", "folders", "diagrams")


# With the session time zone in UTC, Postgres reads the stored naive values as UTC and changes only the
# column type, without rewriting the tables (a USING clause would rewrite them under an exclusive lock).
def upgrade() -> None:
    op.execute("SET LOCAL timezone = 'UTC'")
    for table in SOFT_DELETE_TABLES:
        op.alter_column(
            table,
            "deleted_at",
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=True,
        )


def downgrade() -> None:
    op.execute("SET LOCAL timezone = 'UTC'")
    for table in SOFT_DELETE_TABLES:
        op.alter_column(
            table,
            "deleted_at",
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=True,
        )
