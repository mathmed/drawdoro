import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram_summary import DiagramSummary


class ListDiagramsParams(InputData):
    project_id: uuid.UUID


class ListDiagrams(Usecase[ListDiagramsParams, list[DiagramSummary]]):
    def __init__(self, repo: DiagramRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListDiagramsParams) -> list[DiagramSummary]:
        return await self._repo.list_by_project(params.project_id)
