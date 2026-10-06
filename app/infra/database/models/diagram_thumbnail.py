import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.workspace import Base


# Kept apart from diagrams so storing a preview never bumps the diagram's updated_at, and loading a
# diagram never reads its previews.
class DiagramThumbnailORM(Base):
    __tablename__ = "diagram_thumbnails"

    diagram_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("diagrams.id", ondelete="CASCADE"), primary_key=True
    )
    theme: Mapped[str] = mapped_column(String(10), primary_key=True)
    # Same type as diagrams.updated_at, which it mirrors.
    version: Mapped[datetime]
    image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
