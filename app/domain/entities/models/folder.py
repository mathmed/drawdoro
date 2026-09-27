from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel


class Folder(BaseModel):
    id: str
    project_id: str
    parent_folder_id: str | None = None
    name: str
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
