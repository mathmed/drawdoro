import uuid

from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.documentation_page import DocumentationPage


class UpsertDocumentationPageParams(InputData):
    diagram_id: uuid.UUID
    content: str


class UpsertDocumentationPage(Usecase[UpsertDocumentationPageParams, DocumentationPage]):
    def __init__(self, repo: DocumentationPageRepository) -> None:
        self._repo = repo

    async def execute(self, params: UpsertDocumentationPageParams) -> DocumentationPage:
        page = DocumentationPage(diagram_id=params.diagram_id, content=params.content)
        return await self._repo.upsert(page)
