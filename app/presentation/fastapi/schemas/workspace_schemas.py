import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.presentation.fastapi.schemas.text_schemas import NameStr


class CreateWorkspaceRequest(BaseModel):
    name: NameStr
    slug: NameStr


class UpdateWorkspaceRequest(BaseModel):
    name: NameStr
    slug: NameStr


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
