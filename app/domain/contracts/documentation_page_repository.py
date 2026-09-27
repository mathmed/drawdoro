from abc import ABC, abstractmethod

from app.domain.entities.models.documentation_page import DocumentationPage


class DocumentationPageRepository(ABC):
    @abstractmethod
    def get_by_diagram(self, _diagram_id: str) -> DocumentationPage | None: ...

    @abstractmethod
    def upsert(self, _page: DocumentationPage) -> DocumentationPage: ...
