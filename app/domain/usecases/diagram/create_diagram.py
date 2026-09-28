import uuid
from typing import Any

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram


class CreateDiagramParams(InputData):
    project_id: uuid.UUID
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class CreateDiagram(Usecase[CreateDiagramParams, Diagram]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateDiagramParams) -> Diagram:
        diagram = Diagram(
            project_id=params.project_id,
            name=params.name,
            folder_id=params.folder_id,
            canvas_state=params.canvas_state,
        )
        return await self._repo.create(diagram)
