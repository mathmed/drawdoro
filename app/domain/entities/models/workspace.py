from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel


class Workspace(BaseModel):
    id: str
    name: str
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
