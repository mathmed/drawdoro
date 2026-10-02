import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.constants.revisions import REVISION_SUMMARY_MAX_LENGTH


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
