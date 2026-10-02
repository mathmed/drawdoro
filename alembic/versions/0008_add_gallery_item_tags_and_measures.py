"""add gallery item tags, description and measures

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MEASURE_COLUMNS = ("size_bytes", "height", "width")


# Only nullable columns, or one with a server default: existing items get no tags and no
# description, and the API version running during the rollout keeps reading and writing the table.
def upgrade() -> None:
    op.add_column(
        "gallery_items",
        sa.Column("tags", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
    )
    op.add_column("gallery_items", sa.Column("description", sa.String(500), nullable=True))
    op.add_column("gallery_items", sa.Column("width", sa.Float(), nullable=True))
    op.add_column("gallery_items", sa.Column("height", sa.Float(), nullable=True))
    op.add_column("gallery_items", sa.Column("size_bytes", sa.Integer(), nullable=True))
    # Sizes are cheap to fill in; widths and heights of older items are read from the payload
    # when the item is opened.
    op.execute(
        "UPDATE gallery_items "
        "SET size_bytes = COALESCE(octet_length(image_data), octet_length(CAST(content AS text)))"
    )


def downgrade() -> None:
    for column in (*MEASURE_COLUMNS, "description", "tags"):
        op.drop_column("gallery_items", column)
