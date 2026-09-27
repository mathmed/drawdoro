import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.template import Template


class TemplateRepository(ABC):
    @abstractmethod
    async def create(self, template: Template) -> Template: ...

    @abstractmethod
    async def get_by_id(self, template_id: uuid.UUID) -> Template | None: ...

    @abstractmethod
    async def list_all(self, workspace_id: uuid.UUID | None = None) -> list[Template]: ...

    @abstractmethod
    async def delete(self, template_id: uuid.UUID) -> None: ...
