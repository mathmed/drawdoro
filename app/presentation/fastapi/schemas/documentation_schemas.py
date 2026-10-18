import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.presentation.fastapi.schemas.text_schemas import NulFreeStr


class UpsertDocumentationPageRequest(BaseModel):
    content: NulFreeStr


class DocumentationPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diagram_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime
