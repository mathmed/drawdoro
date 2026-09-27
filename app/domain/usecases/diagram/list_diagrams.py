import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram


class ListDiagramsParams(InputData):
    project_id: uuid.UUID


class ListDiagrams(Usecase[ListDiagramsParams, list[Diagram]]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListDiagramsParams) -> list[Diagram]:
        return await self._repo.list_by_project(params.project_id)
