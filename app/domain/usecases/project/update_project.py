import uuid

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError


class UpdateProjectParams(InputData):
    project_id: uuid.UUID
    name: str
    description: str = ""


class UpdateProject(Usecase[UpdateProjectParams, Project]):
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def execute(self, params: UpdateProjectParams) -> Project:
        project = await self._repo.get_by_id(params.project_id)
        if project is None:
            raise NotFoundError(f"Project {params.project_id} not found")
        project.name = params.name
        project.description = params.description
        return await self._repo.update(project)
