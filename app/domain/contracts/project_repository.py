import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.project import Project


class ProjectRepository(ABC):
    @abstractmethod
    async def create(self, project: Project) -> Project: ...

    @abstractmethod
    async def get_by_id(self, project_id: uuid.UUID) -> Project | None: ...

    @abstractmethod
    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Project]: ...

    @abstractmethod
    async def update(self, project: Project) -> Project: ...

    @abstractmethod
    async def delete(self, project_id: uuid.UUID) -> None: ...
