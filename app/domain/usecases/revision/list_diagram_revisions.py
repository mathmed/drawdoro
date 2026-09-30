import uuid

from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram_revision import DiagramRevision

MAX_LISTED_REVISIONS = 200


class ListDiagramRevisionsParams(InputData):
    diagram_id: uuid.UUID
    limit: int = MAX_LISTED_REVISIONS


class ListDiagramRevisions(Usecase[ListDiagramRevisionsParams, list[DiagramRevision]]):
    def __init__(self, repo: DiagramRevisionRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListDiagramRevisionsParams) -> list[DiagramRevision]:
        limit = max(1, min(params.limit, MAX_LISTED_REVISIONS))
        return await self._repo.list_by_diagram(params.diagram_id, limit)
