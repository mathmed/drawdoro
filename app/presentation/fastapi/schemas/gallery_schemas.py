import base64
import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field, PlainSerializer

from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType

# Stored bytes go out as base64 text; Base64Bytes would try to decode them on the way in.
EncodedBytes = Annotated[
    bytes, PlainSerializer(lambda data: base64.b64encode(data).decode(), return_type=str)
]


class CreateGalleryItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: GalleryItemKind
    content: dict[str, Any] | None = None
    image_base64: Base64Bytes | None = None
    thumbnail_base64: Base64Bytes | None = None


class RenameGalleryItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class GalleryItemSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: GalleryItemKind
    image_mime_type: ImageMimeType | None
    thumbnail_base64: EncodedBytes | None = Field(validation_alias="thumbnail")
    created_at: datetime
    updated_at: datetime


class GalleryItemResponse(GalleryItemSummaryResponse):
    content: dict[str, Any] | None
    image_base64: EncodedBytes | None = Field(validation_alias="image_data")
