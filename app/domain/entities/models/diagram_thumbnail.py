import uuid
from datetime import datetime

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.thumbnail_theme import ThumbnailTheme


# A preview of a diagram in one theme, rendered by an editor's browser.
class DiagramThumbnail(BaseModel):
    diagram_id: uuid.UUID
    theme: ThumbnailTheme
    # The diagram's updated_at the image was rendered from: a render only replaces an older one.
    version: datetime
    # None when the diagram had nothing to draw, or the render did not fit the size limit.
    image: bytes | None = None
    mime_type: ImageMimeType | None = None
