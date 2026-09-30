import json
import uuid
from typing import Any

from app.domain.constants.gallery import GALLERY_MAX_THUMBNAIL_BYTES
from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.gallery_item import GalleryItem
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.errors.domain_errors import InvalidInputError, PayloadTooLargeError
from app.domain.services.gallery_item_name import normalize_gallery_item_name
from app.domain.services.image_type_detector import detect_image_mime_type


class CreateGalleryItemParams(InputData):
    owner_id: uuid.UUID | None = None
    name: str
    kind: GalleryItemKind
    content: dict[str, Any] | None = None
    image_data: bytes | None = None
    thumbnail: bytes | None = None


class CreateGalleryItem(Usecase[CreateGalleryItemParams, GalleryItem]):
    def __init__(self, repo: GalleryItemRepository, limits: GalleryLimits) -> None:
        self._repo = repo
        self._limits = limits

    async def execute(self, params: CreateGalleryItemParams) -> GalleryItem:
        name = normalize_gallery_item_name(params.name)
        _validate_thumbnail(params.thumbnail)
        item = GalleryItem(
            owner_id=params.owner_id, name=name, kind=params.kind, thumbnail=params.thumbnail
        )
        if params.kind == GalleryItemKind.SHAPES:
            item.content = self._validate_shapes(params)
        else:
            item.image_data, item.image_mime_type = self._validate_image(params)
        return await self._repo.create(item)

    def _validate_shapes(self, params: CreateGalleryItemParams) -> dict[str, Any]:
        content = params.content
        if content is None or params.image_data is not None:
            raise InvalidInputError("A shapes item needs content and no image")
        shapes = content.get("shapes")
        if not isinstance(shapes, list) or len(shapes) == 0:
            raise InvalidInputError("A shapes item needs at least one shape")
        size = len(json.dumps(content).encode())
        if size > self._limits.max_shapes_bytes:
            raise PayloadTooLargeError(
                f"The selection is too large ({size} bytes, limit {self._limits.max_shapes_bytes})"
            )
        return content

    def _validate_image(self, params: CreateGalleryItemParams) -> tuple[bytes, ImageMimeType]:
        data = params.image_data
        if data is None or params.content is not None:
            raise InvalidInputError("An image item needs image data and no content")
        if len(data) > self._limits.max_image_bytes:
            raise PayloadTooLargeError(
                f"The image is too large ({len(data)} bytes, limit {self._limits.max_image_bytes})"
            )
        mime_type = detect_image_mime_type(data)
        if mime_type is None:
            raise InvalidInputError("Unsupported image type: use PNG, JPEG, GIF or WebP")
        return data, mime_type


def _validate_thumbnail(thumbnail: bytes | None) -> None:
    if thumbnail is None:
        return
    if len(thumbnail) > GALLERY_MAX_THUMBNAIL_BYTES:
        raise PayloadTooLargeError(
            f"The thumbnail is too large (limit {GALLERY_MAX_THUMBNAIL_BYTES} bytes)"
        )
    if detect_image_mime_type(thumbnail) != ImageMimeType.PNG:
        raise InvalidInputError("The thumbnail must be a PNG image")
