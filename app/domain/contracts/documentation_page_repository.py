import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.documentation_page import DocumentationPage


class DocumentationPageRepository(ABC):
    @abstractmethod
    async def get_by_diagram(self, diagram_id: uuid.UUID) -> DocumentationPage | None: ...

    @abstractmethod
    async def upsert(self, page: DocumentationPage) -> DocumentationPage: ...
