import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.documentation.get_documentation_page import (
    GetDocumentationPage,
    GetDocumentationPageParams,
)
from app.domain.usecases.documentation.upsert_documentation_page import (
    UpsertDocumentationPage,
    UpsertDocumentationPageParams,
)
from app.presentation.factories.documentation_factories import (
    get_documentation_page_factory,
    upsert_documentation_page_factory,
)
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.documentation_schemas import (
    DocumentationPageResponse,
    UpsertDocumentationPageRequest,
)

router = APIRouter(
    prefix="/diagrams/{diagram_id}/documentation",
    tags=["documentation"],
    dependencies=[Depends(require_workspace_access)],
)


@router.get("", response_model=DocumentationPageResponse)
async def get_documentation_page(
    diagram_id: uuid.UUID,
    use_case: GetDocumentationPage = Depends(get_documentation_page_factory),
) -> DocumentationPageResponse:
    page = await use_case.execute(GetDocumentationPageParams(diagram_id=diagram_id))
    return DocumentationPageResponse.model_validate(page)


@router.put("", response_model=DocumentationPageResponse)
async def upsert_documentation_page(
    diagram_id: uuid.UUID,
    body: UpsertDocumentationPageRequest,
    use_case: UpsertDocumentationPage = Depends(upsert_documentation_page_factory),
) -> DocumentationPageResponse:
    page = await use_case.execute(
        UpsertDocumentationPageParams(diagram_id=diagram_id, content=body.content)
    )
    return DocumentationPageResponse.model_validate(page)
