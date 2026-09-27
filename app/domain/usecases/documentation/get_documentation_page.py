import uuid

from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.documentation_page import DocumentationPage
from app.domain.errors.domain_errors import NotFoundError


class GetDocumentationPageParams(InputData):
    diagram_id: uuid.UUID


class GetDocumentationPage(Usecase[GetDocumentationPageParams, DocumentationPage]):
    def __init__(self, repo: DocumentationPageRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetDocumentationPageParams) -> DocumentationPage:
        page = await self._repo.get_by_diagram(params.diagram_id)
        if page is None:
            raise NotFoundError(f"Documentation page for diagram {params.diagram_id} not found")
        return page
