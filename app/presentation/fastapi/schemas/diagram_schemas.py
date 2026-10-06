import uuid
from datetime import datetime
from typing import Any

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field

from app.domain.constants.revisions import REVISION_SUMMARY_MAX_LENGTH
from app.domain.enums.image_mime_type import ImageMimeType
from app.presentation.fastapi.schemas.gallery_schemas import EncodedBytes


class CreateDiagramRequest(BaseModel):
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class UpdateDiagramRequest(BaseModel):
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None
    # Shown in the diagram's history next to the change; agents describe what they did.
    revision_summary: str | None = Field(default=None, max_length=REVISION_SUMMARY_MAX_LENGTH)


class DiagramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    folder_id: uuid.UUID | None
    name: str
    canvas_state: dict[str, Any] | None
    semantic_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class DiagramSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    folder_id: uuid.UUID | None
    name: str
    created_at: datetime
    updated_at: datetime


# Previews rendered by an editor; a theme sent as null has nothing to show (an empty diagram).
class SaveDiagramThumbnailRequest(BaseModel):
    # The diagram's updated_at the images were rendered from, as the API returned it.
    version: datetime
    light_base64: Base64Bytes | None = None
    dark_base64: Base64Bytes | None = None


class DiagramThumbnailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    diagram_id: uuid.UUID
    version: datetime
    mime_type: ImageMimeType
    image_base64: EncodedBytes = Field(validation_alias="image")


class ShareDiagramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    share_token: str


# Public payload served to anyone holding the share link, including guests. It purposely
# omits workspace/project identifiers and exposes only what the shared canvas needs to render.
class SharedDiagramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    canvas_state: dict[str, Any] | None
    semantic_metadata: dict[str, Any] | None
