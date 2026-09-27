import uuid

from app.domain.contracts.template_repository import TemplateRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.template import Template


class ListTemplatesParams(InputData):
    workspace_id: uuid.UUID | None = None


class ListTemplates(Usecase[ListTemplatesParams, list[Template]]):
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListTemplatesParams) -> list[Template]:
        return await self._repo.list_all(params.workspace_id)
