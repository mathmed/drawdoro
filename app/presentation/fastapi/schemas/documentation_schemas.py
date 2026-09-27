import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UpsertDocumentationPageRequest(BaseModel):
    content: str


class DocumentationPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diagram_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime
