import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.presentation.fastapi.schemas.text_schemas import NulFreeStr


class CreateWorkspaceRequest(BaseModel):
    name: NulFreeStr
    slug: NulFreeStr


class UpdateWorkspaceRequest(BaseModel):
    name: NulFreeStr
    slug: NulFreeStr


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
