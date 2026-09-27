from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel


class Project(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str = ""
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
