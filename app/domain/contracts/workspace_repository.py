from abc import ABC, abstractmethod

from app.domain.entities.models.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    def create(self, _workspace: Workspace) -> Workspace: ...

    @abstractmethod
    def get_by_id(self, _workspace_id: str) -> Workspace | None: ...

    @abstractmethod
    def list_all(self) -> list[Workspace]: ...

    @abstractmethod
    def update(self, _workspace: Workspace) -> Workspace: ...

    @abstractmethod
    def delete(self, _workspace_id: str) -> None: ...
