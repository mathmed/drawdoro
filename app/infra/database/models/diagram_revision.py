import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.constants.user import PICTURE_URL_MAX_LENGTH
from app.infra.database.models.workspace import Base


class DiagramRevisionORM(Base):
    __tablename__ = "diagram_revisions"
    __table_args__ = (Index("ix_diagram_revisions_diagram_updated", "diagram_id", "updated_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    diagram_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("diagrams.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(20))
    origin: Mapped[str] = mapped_column(String(20))
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_picture_url: Mapped[str | None] = mapped_column(
        String(PICTURE_URL_MAX_LENGTH), nullable=True
    )
    agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    restored_from_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("diagram_revisions.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    canvas_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    semantic_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
