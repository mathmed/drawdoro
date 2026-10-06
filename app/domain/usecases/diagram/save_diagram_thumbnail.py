import uuid
from datetime import datetime

from app.domain.constants.thumbnails import DIAGRAM_THUMBNAIL_MAX_BYTES
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_thumbnail_repository import DiagramThumbnailRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.thumbnail_theme import ThumbnailTheme
from app.domain.errors.domain_errors import InvalidInputError, NotFoundError, PayloadTooLargeError
from app.domain.services.image_type_detector import detect_image_mime_type

# Browsers that can't encode WebP fall back to PNG; both keep the transparent background.
THUMBNAIL_MIME_TYPES = {ImageMimeType.PNG, ImageMimeType.WEBP}


class SaveDiagramThumbnailParams(InputData):
    diagram_id: uuid.UUID
    version: datetime
    # None for a theme means there is nothing to show in it: an empty diagram sends neither.
    light: bytes | None = None
    dark: bytes | None = None


class SaveDiagramThumbnail(Usecase[SaveDiagramThumbnailParams, None]):
    def __init__(self, diagrams: DiagramRepository, thumbnails: DiagramThumbnailRepository) -> None:
        self._diagrams = diagrams
        self._thumbnails = thumbnails

    async def execute(self, params: SaveDiagramThumbnailParams) -> None:
        images = {ThumbnailTheme.LIGHT: params.light, ThumbnailTheme.DARK: params.dark}
        thumbnails = [
            _thumbnail(params.diagram_id, params.version, theme, image)
            for theme, image in images.items()
        ]
        if not await self._diagrams.exists(params.diagram_id):
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        await self._thumbnails.save(thumbnails)


def _thumbnail(
    diagram_id: uuid.UUID, version: datetime, theme: ThumbnailTheme, image: bytes | None
) -> DiagramThumbnail:
    if image is None:
        return DiagramThumbnail(diagram_id=diagram_id, theme=theme, version=version)
    if len(image) > DIAGRAM_THUMBNAIL_MAX_BYTES:
        raise PayloadTooLargeError(
            f"The {theme} thumbnail is too large (limit {DIAGRAM_THUMBNAIL_MAX_BYTES} bytes)"
        )
    mime_type = detect_image_mime_type(image)
    if mime_type not in THUMBNAIL_MIME_TYPES:
        raise InvalidInputError(f"The {theme} thumbnail must be a PNG or WebP image")
    return DiagramThumbnail(
        diagram_id=diagram_id, theme=theme, version=version, image=image, mime_type=mime_type
    )
