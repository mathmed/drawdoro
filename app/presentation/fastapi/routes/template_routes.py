import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.template.create_template import CreateTemplate, CreateTemplateParams
from app.domain.usecases.template.delete_template import DeleteTemplate, DeleteTemplateParams
from app.domain.usecases.template.get_template import GetTemplate, GetTemplateParams
from app.domain.usecases.template.list_templates import ListTemplates, ListTemplatesParams
from app.presentation.factories.template_factories import (
    create_template_factory,
    delete_template_factory,
    get_template_factory,
    list_templates_factory,
)
from app.presentation.fastapi.schemas.template_schemas import (
    CreateTemplateRequest,
    TemplateResponse,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    use_case: ListTemplates = Depends(list_templates_factory),
) -> list[TemplateResponse]:
    templates = await use_case.execute(ListTemplatesParams())
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: CreateTemplateRequest,
    use_case: CreateTemplate = Depends(create_template_factory),
) -> TemplateResponse:
    template = await use_case.execute(
        CreateTemplateParams(
            name=body.name,
            description=body.description,
            workspace_id=body.workspace_id,
            canvas_state=body.canvas_state,
        )
    )
    return TemplateResponse.model_validate(template)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    use_case: GetTemplate = Depends(get_template_factory),
) -> TemplateResponse:
    template = await use_case.execute(GetTemplateParams(template_id=template_id))
    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    use_case: DeleteTemplate = Depends(delete_template_factory),
) -> None:
    await use_case.execute(DeleteTemplateParams(template_id=template_id))
