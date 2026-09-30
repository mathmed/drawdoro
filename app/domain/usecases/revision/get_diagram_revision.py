import uuid

from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.errors.domain_errors import NotFoundError


class GetDiagramRevisionParams(InputData):
    diagram_id: uuid.UUID
    revision_id: uuid.UUID


class GetDiagramRevision(Usecase[GetDiagramRevisionParams, DiagramRevision]):
    def __init__(self, repo: DiagramRevisionRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetDiagramRevisionParams) -> DiagramRevision:
        revision = await self._repo.get(params.diagram_id, params.revision_id)
        if revision is None:
            raise NotFoundError(f"Revision {params.revision_id} not found")
        return revision
