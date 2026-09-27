from abc import ABC, abstractmethod

from app.domain.entities.models.diagram import Diagram


class DiagramRepository(ABC):
    @abstractmethod
    def create(self, _diagram: Diagram) -> Diagram: ...

    @abstractmethod
    def get_by_id(self, _diagram_id: str) -> Diagram | None: ...

    @abstractmethod
    def list_by_project(self, _project_id: str) -> list[Diagram]: ...

    @abstractmethod
    def list_by_folder(self, _folder_id: str) -> list[Diagram]: ...

    @abstractmethod
    def update(self, _diagram: Diagram) -> Diagram: ...

    @abstractmethod
    def delete(self, _diagram_id: str) -> None: ...
