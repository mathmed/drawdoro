import uuid
from typing import Any

from app.domain.contracts.template_repository import TemplateRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.template import Template


class CreateTemplateParams(InputData):
    name: str
    description: str = ""
    workspace_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class CreateTemplate(Usecase[CreateTemplateParams, Template]):
    def __init__(self, repo: TemplateRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateTemplateParams) -> Template:
        template = Template(
            name=params.name,
            description=params.description,
            workspace_id=params.workspace_id,
            canvas_state=params.canvas_state,
        )
        return await self._repo.create(template)
