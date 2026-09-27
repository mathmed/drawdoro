import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel


class CustomShape(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID
    name: str
    shape_definition: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
