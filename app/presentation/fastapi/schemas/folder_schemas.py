import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.presentation.fastapi.schemas.text_schemas import NulFreeStr


class CreateFolderRequest(BaseModel):
    name: NulFreeStr
    parent_folder_id: uuid.UUID | None = None


class UpdateFolderRequest(BaseModel):
    name: NulFreeStr
    parent_folder_id: uuid.UUID | None = None


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    parent_folder_id: uuid.UUID | None
    name: str
    created_at: datetime
    updated_at: datetime
