import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.folder import Folder


class FolderRepository(ABC):
    @abstractmethod
    async def create(self, folder: Folder) -> Folder: ...

    @abstractmethod
    async def get_by_id(self, folder_id: uuid.UUID) -> Folder | None: ...

    @abstractmethod
    async def list_by_project(self, project_id: uuid.UUID) -> list[Folder]: ...

    @abstractmethod
    async def update(self, folder: Folder) -> Folder: ...

    @abstractmethod
    async def delete(self, folder_id: uuid.UUID) -> None: ...
