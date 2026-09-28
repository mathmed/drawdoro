import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CreateDiagramRequest(BaseModel):
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class UpdateDiagramRequest(BaseModel):
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None


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
