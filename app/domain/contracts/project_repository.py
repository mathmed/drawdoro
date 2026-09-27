from abc import ABC, abstractmethod

from app.domain.entities.models.project import Project


class ProjectRepository(ABC):
    @abstractmethod
    def create(self, _project: Project) -> Project: ...

    @abstractmethod
    def get_by_id(self, _project_id: str) -> Project | None: ...

    @abstractmethod
    def list_by_workspace(self, _workspace_id: str) -> list[Project]: ...

    @abstractmethod
    def update(self, _project: Project) -> Project: ...

    @abstractmethod
    def delete(self, _project_id: str) -> None: ...
