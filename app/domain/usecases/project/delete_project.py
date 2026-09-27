import uuid

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import NotFoundError


class DeleteProjectParams(InputData):
    project_id: uuid.UUID


class DeleteProject(Usecase[DeleteProjectParams, None]):
    def __init__(self, repo: ProjectRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteProjectParams) -> None:
        project = await self._repo.get_by_id(params.project_id)
        if project is None:
            raise NotFoundError(f"Project {params.project_id} not found")
        await self._repo.delete(params.project_id)
