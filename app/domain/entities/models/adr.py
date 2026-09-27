from datetime import UTC, datetime

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.adr_status import AdrStatus


class Adr(BaseModel):
    id: str
    diagram_id: str
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus = AdrStatus.PROPOSED
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)
