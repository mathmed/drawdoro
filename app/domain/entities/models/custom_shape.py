from datetime import UTC, datetime
from typing import Any

from app.domain.entities.models.base_model import BaseModel


class CustomShape(BaseModel):
    id: str
    owner_id: str
    workspace_id: str | None = None
    name: str
    shape_definition: dict[str, Any]
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
