from app.domain.entities.models.base_model import BaseModel
from app.domain.entities.models.diagram_summary import DiagramSummary
from app.domain.entities.models.folder import Folder


class ProjectTree(BaseModel):
    folders: list[Folder]
    diagrams: list[DiagramSummary]
