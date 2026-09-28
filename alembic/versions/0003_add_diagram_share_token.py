"""add diagram share token

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("diagrams", sa.Column("share_token", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_diagrams_share_token", "diagrams", ["share_token"])
    op.create_index("ix_diagrams_share_token", "diagrams", ["share_token"])


def downgrade() -> None:
    op.drop_index("ix_diagrams_share_token", table_name="diagrams")
    op.drop_constraint("uq_diagrams_share_token", "diagrams", type_="unique")
    op.drop_column("diagrams", "share_token")
