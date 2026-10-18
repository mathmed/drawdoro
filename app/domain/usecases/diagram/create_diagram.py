import uuid
from typing import Any

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.services.project_placement import ProjectPlacement


class CreateDiagramParams(InputData):
    project_id: uuid.UUID
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class CreateDiagram(Usecase[CreateDiagramParams, Diagram]):
    def __init__(self, repo: DiagramRepository, placement: ProjectPlacement) -> None:
        self._repo = repo
        self._placement = placement

    async def execute(self, params: CreateDiagramParams) -> Diagram:
        await self._placement.check_new(params.project_id, params.folder_id)
        diagram = Diagram(
            project_id=params.project_id,
            name=params.name,
            folder_id=params.folder_id,
            canvas_state=params.canvas_state,
        )
        return await self._repo.create(diagram)
