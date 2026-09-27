import uuid

from app.domain.contracts.template_repository import TemplateRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import NotFoundError


class DeleteTemplateParams(InputData):
    template_id: uuid.UUID


class DeleteTemplate(Usecase[DeleteTemplateParams, None]):
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteTemplateParams) -> None:
        template = await self._repo.get_by_id(params.template_id)
        if template is None:
            raise NotFoundError(f"Template {params.template_id} not found")
        await self._repo.delete(params.template_id)
