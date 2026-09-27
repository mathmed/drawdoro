from datetime import UTC, datetime
from typing import Any

from app.domain.entities.models.base_model import BaseModel


class Template(BaseModel):
    id: str
    workspace_id: str | None = None
    name: str
    description: str = ""
    canvas_state: dict[str, Any] | None = None
    is_global: bool = False
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
