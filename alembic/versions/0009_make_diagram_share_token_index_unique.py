"""make the diagram share token index unique

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-05 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# 0003 created a unique constraint plus a plain index on the same column, while the model declares a
# single unique index. The constraint is dropped only after the unique index exists, so share tokens
# stay unique at every step.
def upgrade() -> None:
    op.drop_index("ix_diagrams_share_token", table_name="diagrams")
    op.create_index("ix_diagrams_share_token", "diagrams", ["share_token"], unique=True)
    op.drop_constraint("uq_diagrams_share_token", "diagrams", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_diagrams_share_token", "diagrams", ["share_token"])
    op.drop_index("ix_diagrams_share_token", table_name="diagrams")
    op.create_index("ix_diagrams_share_token", "diagrams", ["share_token"])
