import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel


class Diagram(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    project_id: uuid.UUID
    folder_id: uuid.UUID | None = None
    name: str
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None
