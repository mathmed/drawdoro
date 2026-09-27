import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CreateTemplateRequest(BaseModel):
    name: str
    description: str = ""
    workspace_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID | None
    name: str
    description: str
    canvas_state: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
