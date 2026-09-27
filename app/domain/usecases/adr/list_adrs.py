import uuid

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.adr import Adr


class ListAdrsParams(InputData):
    diagram_id: uuid.UUID


class ListAdrs(Usecase[ListAdrsParams, list[Adr]]):
    def __init__(self, repo: AdrRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListAdrsParams) -> list[Adr]:
        return await self._repo.list_by_diagram(params.diagram_id)
