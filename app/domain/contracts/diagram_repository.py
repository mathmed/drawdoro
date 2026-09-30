import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_summary import DiagramSummary


class DiagramRepository(ABC):
    @abstractmethod
    async def create(self, diagram: Diagram) -> Diagram: ...

    @abstractmethod
    async def get_by_id(self, diagram_id: uuid.UUID) -> Diagram | None: ...

    @abstractmethod
    async def get_by_share_token(self, share_token: str) -> Diagram | None: ...

    @abstractmethod
    async def set_share_token(self, diagram_id: uuid.UUID, share_token: str) -> Diagram: ...

    @abstractmethod
    async def list_by_project(self, project_id: uuid.UUID) -> list[DiagramSummary]: ...

    @abstractmethod
    async def list_by_folder(self, folder_id: uuid.UUID) -> list[Diagram]: ...

    @abstractmethod
    async def update(self, diagram: Diagram) -> Diagram: ...

    @abstractmethod
    async def delete(self, diagram_id: uuid.UUID) -> None: ...
