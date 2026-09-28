"""remove templates, ADRs and diagram code sources

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("adrs")
    op.drop_table("templates")
    op.drop_column("diagrams", "mermaid_source")
    op.drop_column("diagrams", "d2_source")


def downgrade() -> None:
    op.add_column("diagrams", sa.Column("d2_source", sa.Text(), nullable=True))
    op.add_column("diagrams", sa.Column("mermaid_source", sa.Text(), nullable=True))
    op.create_table(
        "templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("canvas_state", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "adrs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("diagram_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("consequences", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["diagram_id"], ["diagrams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
