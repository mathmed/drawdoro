import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.documentation_page import DocumentationPage
from app.domain.errors.domain_errors import NotFoundError


class UpsertDocumentationPageParams(InputData):
    diagram_id: uuid.UUID
    content: str


class UpsertDocumentationPage(Usecase[UpsertDocumentationPageParams, DocumentationPage]):
    def __init__(self, repo: DocumentationPageRepository, diagrams: DiagramRepository) -> None:
        self._repo = repo
        self._diagrams = diagrams

    async def execute(self, params: UpsertDocumentationPageParams) -> DocumentationPage:
        # Workspace access already checks it for people; the service key and auth off skip that.
        if not await self._diagrams.exists(params.diagram_id):
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        page = DocumentationPage(diagram_id=params.diagram_id, content=params.content)
        return await self._repo.upsert(page)
