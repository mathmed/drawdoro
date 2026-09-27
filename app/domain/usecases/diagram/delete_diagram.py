import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import NotFoundError


class DeleteDiagramParams(InputData):
    diagram_id: uuid.UUID


class DeleteDiagram(Usecase[DeleteDiagramParams, None]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteDiagramParams) -> None:
        diagram = await self._repo.get_by_id(params.diagram_id)
        if diagram is None:
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        await self._repo.delete(params.diagram_id)
