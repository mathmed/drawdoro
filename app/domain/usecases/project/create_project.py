import uuid

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.project import Project


class CreateProjectParams(InputData):
    workspace_id: uuid.UUID
    name: str
    description: str = ""


class CreateProject(Usecase[CreateProjectParams, Project]):
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateProjectParams) -> Project:
        project = Project(
            workspace_id=params.workspace_id, name=params.name, description=params.description
        )
        return await self._repo.create(project)
