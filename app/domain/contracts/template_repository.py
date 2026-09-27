from abc import ABC, abstractmethod

from app.domain.entities.models.template import Template


class TemplateRepository(ABC):
    @abstractmethod
    def create(self, _template: Template) -> Template: ...

    @abstractmethod
    def get_by_id(self, _template_id: str) -> Template | None: ...

    @abstractmethod
    def list_all(self, _workspace_id: str | None = None) -> list[Template]: ...

    @abstractmethod
    def update(self, _template: Template) -> Template: ...

    @abstractmethod
    def delete(self, _template_id: str) -> None: ...
