import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateWorkspaceRequest(BaseModel):
    name: str
    slug: str


class UpdateWorkspaceRequest(BaseModel):
    name: str
    slug: str


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
