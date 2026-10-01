"""add comment resolution and agent authorship

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FK_RESOLVED_BY = "fk_comments_resolved_by_id_users"


# Only nullable columns, or one with a server default: existing comments stay open and written by
# people, and the API version running during the rollout keeps reading and writing the table.
def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("origin", sa.String(20), server_default=sa.text("'human'"), nullable=False),
    )
    op.add_column("comments", sa.Column("agent_name", sa.String(255), nullable=True))
    op.add_column("comments", sa.Column("agent_label", sa.String(255), nullable=True))
    op.add_column("comments", sa.Column("api_key_id", sa.Uuid(), nullable=True))
    op.add_column("comments", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("comments", sa.Column("resolved_by_id", sa.Uuid(), nullable=True))
    op.add_column("comments", sa.Column("resolved_by_origin", sa.String(20), nullable=True))
    op.add_column("comments", sa.Column("resolved_by_agent_name", sa.String(255), nullable=True))
    op.add_column("comments", sa.Column("resolved_by_agent_label", sa.String(255), nullable=True))
    op.create_foreign_key(
        FK_RESOLVED_BY, "comments", "users", ["resolved_by_id"], ["id"], ondelete="SET NULL"
    )
    # Comments on the whole diagram have no shape.
    op.alter_column("comments", "element_id", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE comments SET element_id = '' WHERE element_id IS NULL")
    op.alter_column("comments", "element_id", existing_type=sa.String(255), nullable=False)
    op.drop_constraint(FK_RESOLVED_BY, "comments", type_="foreignkey")
    for column in (
        "resolved_by_agent_label",
        "resolved_by_agent_name",
        "resolved_by_origin",
        "resolved_by_id",
        "resolved_at",
        "api_key_id",
        "agent_label",
        "agent_name",
        "origin",
    ):
        op.drop_column("comments", column)
