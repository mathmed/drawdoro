import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel


class User(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
