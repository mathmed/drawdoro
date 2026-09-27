import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError


class GetDiagramParams(InputData):
    diagram_id: uuid.UUID


class GetDiagram(Usecase[GetDiagramParams, Diagram]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetDiagramParams) -> Diagram:
        diagram = await self._repo.get_by_id(params.diagram_id)
        if diagram is None:
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        return diagram
