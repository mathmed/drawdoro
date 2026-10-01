import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType


class GalleryItemSummary(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # None only when authentication is disabled (local development) and there is no signed-in user.
    owner_id: uuid.UUID | None = None
    name: str
    kind: GalleryItemKind
    # Lower-case words that make the item findable; empty for items saved before tags existed.
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    image_mime_type: ImageMimeType | None = None
    thumbnail: bytes | None = None
    # Pixels for images, canvas units for shapes; None for items saved before they were measured.
    width: float | None = None
    height: float | None = None
    # Bytes of the image, or of the shapes as JSON.
    size_bytes: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GalleryItem(GalleryItemSummary):
    # tldraw content (shapes, bindings, assets) for "shapes" items.
    content: dict[str, Any] | None = None
    image_data: bytes | None = None
