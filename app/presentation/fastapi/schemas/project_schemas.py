import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.presentation.fastapi.schemas.text_schemas import NulFreeStr


class CreateProjectRequest(BaseModel):
    name: NulFreeStr
    description: NulFreeStr = ""


class UpdateProjectRequest(BaseModel):
    name: NulFreeStr
    description: NulFreeStr = ""


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
