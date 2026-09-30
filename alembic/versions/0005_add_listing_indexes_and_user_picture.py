"""add foreign key indexes for listings and the user profile photo

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Postgres does not index foreign keys on its own; every listing and access check filters on these.
INDEXES = [
    ("projects", "workspace_id"),
    ("folders", "project_id"),
    ("folders", "parent_folder_id"),
    ("diagrams", "project_id"),
    ("diagrams", "folder_id"),
    ("comments", "diagram_id"),
    ("workspace_members", "workspace_id"),
    ("workspace_members", "user_id"),
]


def upgrade() -> None:
    for table, column in INDEXES:
        op.create_index(f"ix_{table}_{column}", table, [column])
    op.add_column("users", sa.Column("picture_url", sa.String(2048), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "picture_url")
    for table, column in reversed(INDEXES):
        op.drop_index(f"ix_{table}_{column}", table_name=table)
