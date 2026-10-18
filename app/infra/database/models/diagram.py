import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.constants.names import NAME_MAX_LENGTH
from app.infra.database.models.workspace import Base


class DiagramORM(Base):
    __tablename__ = "diagrams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    canvas_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    semantic_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    share_token: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
