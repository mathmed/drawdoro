from pydantic import BaseModel, ConfigDict

from app.presentation.fastapi.schemas.diagram_schemas import DiagramSummaryResponse
from app.presentation.fastapi.schemas.folder_schemas import FolderResponse


class ProjectTreeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    folders: list[FolderResponse]
    diagrams: list[DiagramSummaryResponse]
