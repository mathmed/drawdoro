import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel


class Comment(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    diagram_id: uuid.UUID
    element_id: str
    content: str
    author_id: uuid.UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
