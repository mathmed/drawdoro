import uuid

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.project import Project


class ListProjectsParams(InputData):
    workspace_id: uuid.UUID


class ListProjects(Usecase[ListProjectsParams, list[Project]]):
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListProjectsParams) -> list[Project]:
        return await self._repo.list_by_workspace(params.workspace_id)
