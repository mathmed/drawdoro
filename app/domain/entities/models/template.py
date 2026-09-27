import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel


class Template(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID | None = None
    name: str
    description: str = ""
    canvas_state: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
