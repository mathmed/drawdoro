import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def create(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None: ...

    @abstractmethod
    async def list_all(self) -> list[Workspace]: ...

    @abstractmethod
    async def list_for_user(self, user_id: uuid.UUID) -> list[Workspace]: ...

    @abstractmethod
    async def list_without_members(self) -> list[Workspace]: ...

    @abstractmethod
    async def update(self, workspace: Workspace) -> Workspace: ...

    @abstractmethod
    async def delete(self, workspace_id: uuid.UUID) -> None: ...
