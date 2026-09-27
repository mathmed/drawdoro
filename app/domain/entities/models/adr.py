import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.adr_status import AdrStatus


class Adr(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    diagram_id: uuid.UUID
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus = AdrStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
