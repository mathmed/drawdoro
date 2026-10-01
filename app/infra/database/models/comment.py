import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.constants.comments import COMMENT_ELEMENT_ID_MAX_LENGTH
from app.infra.database.models.workspace import Base


class CommentORM(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    diagram_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagrams.id", ondelete="CASCADE"), index=True
    )
    element_id: Mapped[str | None] = mapped_column(
        String(COMMENT_ELEMENT_ID_MAX_LENGTH), nullable=True
    )
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    origin: Mapped[str] = mapped_column(String(20), server_default=text("'human'"))
    agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # No foreign key on purpose: authorship must outlive the key, so an agent never inherits it.
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_by_origin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resolved_by_agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_by_agent_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
