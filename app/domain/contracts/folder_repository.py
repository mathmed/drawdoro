from abc import ABC, abstractmethod

from app.domain.entities.models.folder import Folder


class FolderRepository(ABC):
    @abstractmethod
    def create(self, _folder: Folder) -> Folder: ...

    @abstractmethod
    def get_by_id(self, _folder_id: str) -> Folder | None: ...

    @abstractmethod
    def list_by_project(self, _project_id: str) -> list[Folder]: ...

    @abstractmethod
    def update(self, _folder: Folder) -> Folder: ...

    @abstractmethod
    def delete(self, _folder_id: str) -> None: ...
