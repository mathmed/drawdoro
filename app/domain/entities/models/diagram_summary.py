import uuid
from datetime import datetime

from app.domain.entities.models.base_model import BaseModel


# What listings need to show a diagram, without the (large) canvas snapshot.
class DiagramSummary(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    folder_id: uuid.UUID | None = None
    name: str
    created_at: datetime
    updated_at: datetime
