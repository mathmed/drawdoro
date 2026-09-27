import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums.adr_status import AdrStatus


class CreateAdrRequest(BaseModel):
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus = AdrStatus.PROPOSED


class UpdateAdrRequest(BaseModel):
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus


class AdrResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diagram_id: uuid.UUID
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus
    created_at: datetime
    updated_at: datetime
