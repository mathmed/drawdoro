from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel


class DocumentationPage(BaseModel):
    id: str
    diagram_id: str
    content: str = ""
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
