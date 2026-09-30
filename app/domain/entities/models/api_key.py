import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel


# A personal key that lets an agent (the MCP server) act as its owner. Only its hash is stored.
class ApiKey(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    label: str
    # First characters of the secret, so people can tell their keys apart.
    prefix: str
    key_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
