from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel


class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
