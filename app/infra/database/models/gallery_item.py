import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, LargeBinary, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.database.models.workspace import Base


class GalleryItemORM(Base):
    __tablename__ = "gallery_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(20))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    image_mime_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    thumbnail: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
