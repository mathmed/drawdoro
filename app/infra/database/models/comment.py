import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.workspace import Base


class CommentORM(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    diagram_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("diagrams.id", ondelete="CASCADE"))
    element_id: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
