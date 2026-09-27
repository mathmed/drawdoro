from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel


class Comment(BaseModel):
    id: str
    diagram_id: str
    author_id: str
    element_id: str
    content: str
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
