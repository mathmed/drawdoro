"""add diagram thumbnails

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "diagram_thumbnails",
        sa.Column("diagram_id", sa.Uuid(), nullable=False),
        sa.Column("theme", sa.String(10), nullable=False),
        sa.Column("version", sa.DateTime(), nullable=False),
        sa.Column("image", sa.LargeBinary(), nullable=True),
        sa.Column("mime_type", sa.String(50), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["diagram_id"], ["diagrams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("diagram_id", "theme"),
    )


def downgrade() -> None:
    op.drop_table("diagram_thumbnails")
