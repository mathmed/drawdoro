from datetime import UTC, datetime
from typing import Any

from app.domain.entities.models.base_model import BaseModel


class Diagram(BaseModel):
    id: str
    project_id: str
    folder_id: str | None = None
    name: str
    canvas_state: dict[str, Any] | None = None
    mermaid_source: str | None = None
    d2_source: str | None = None
    semantic_metadata: dict[str, Any] | None = None
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
