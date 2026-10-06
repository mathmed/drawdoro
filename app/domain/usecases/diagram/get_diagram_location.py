import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.errors.domain_errors import NotFoundError


class GetDiagramLocationParams(InputData):
    diagram_id: uuid.UUID


class GetDiagramLocation(Usecase[GetDiagramLocationParams, DiagramLocation]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetDiagramLocationParams) -> DiagramLocation:
        location = await self._repo.get_location(params.diagram_id)
        if location is None:
            raise NotFoundError("Diagram not found")
        return location
