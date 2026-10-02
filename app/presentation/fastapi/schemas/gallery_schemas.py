import base64
import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field, PlainSerializer

from app.domain.constants.canvas import CANVAS_DEFAULT_GAP, CANVAS_MAX_COORDINATE
from app.domain.constants.gallery import (
    GALLERY_MAX_DESCRIPTION_LENGTH,
    GALLERY_MAX_NAME_LENGTH,
    GALLERY_MAX_TAG_LENGTH,
    GALLERY_MAX_TAGS,
)
from app.domain.constants.revisions import REVISION_SUMMARY_MAX_LENGTH
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.placement_side import PlacementSide

# Stored bytes go out as base64 text; Base64Bytes would try to decode them on the way in.
EncodedBytes = Annotated[
    bytes, PlainSerializer(lambda data: base64.b64encode(data).decode(), return_type=str)
]
# Raw tags, before normalisation: the length cap leaves room for spaces that get collapsed.
RawTags = Annotated[
    list[Annotated[str, Field(max_length=GALLERY_MAX_TAG_LENGTH * 2)]],
    Field(max_length=GALLERY_MAX_TAGS * 2),
]
# A canvas is JSON: NaN and Infinity, which Python's JSON parser accepts, can't be stored in it.
Coordinate = Annotated[
    float, Field(ge=-CANVAS_MAX_COORDINATE, le=CANVAS_MAX_COORDINATE, allow_inf_nan=False)
]


class CreateGalleryItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=GALLERY_MAX_NAME_LENGTH)
    kind: GalleryItemKind
    content: dict[str, Any] | None = None
    image_base64: Base64Bytes | None = None
    thumbnail_base64: Base64Bytes | None = None
    tags: RawTags = []
    description: str | None = Field(default=None, max_length=GALLERY_MAX_DESCRIPTION_LENGTH)


# Every field is optional and only the ones sent change; {"name": ...} alone still renames.
class UpdateGalleryItemRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=GALLERY_MAX_NAME_LENGTH)
    tags: RawTags | None = None
    # An empty string clears the description.
    description: str | None = Field(default=None, max_length=GALLERY_MAX_DESCRIPTION_LENGTH)


class GalleryItemSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: GalleryItemKind
    tags: list[str]
    description: str | None
    image_mime_type: ImageMimeType | None
    thumbnail_base64: EncodedBytes | None = Field(validation_alias="thumbnail")
    width: float | None
    height: float | None
    size_bytes: int | None
    created_at: datetime
    updated_at: datetime


class GalleryItemResponse(GalleryItemSummaryResponse):
    content: dict[str, Any] | None
    image_base64: EncodedBytes | None = Field(validation_alias="image_data")


class InsertGalleryItemRequest(BaseModel):
    item_id: uuid.UUID
    x: Coordinate | None = None
    y: Coordinate | None = None
    near_shape_id: str | None = Field(default=None, max_length=255)
    side: PlacementSide = PlacementSide.RIGHT
    gap: float = Field(default=CANVAS_DEFAULT_GAP, ge=0, le=10_000, allow_inf_nan=False)
    scale: float = Field(default=1, gt=0, allow_inf_nan=False)
    revision_summary: str | None = Field(default=None, max_length=REVISION_SUMMARY_MAX_LENGTH)


# The saved canvas is not echoed back: it can be megabytes, and the caller only needs the ids.
class GalleryInsertionResponse(BaseModel):
    diagram_id: uuid.UUID
    item_id: uuid.UUID
    updated_at: datetime
    created_ids: list[str]
    root_shape_ids: list[str]
    x: float
    y: float
    width: float
    height: float
