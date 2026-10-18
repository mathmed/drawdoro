import uuid

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError


class CreateProjectParams(InputData):
    workspace_id: uuid.UUID
    name: str
    description: str = ""


class CreateProject(Usecase[CreateProjectParams, Project]):
    def __init__(self, repo: ProjectRepository, workspaces: WorkspaceRepository) -> None:
        self._repo = repo
        self._workspaces = workspaces

    async def execute(self, params: CreateProjectParams) -> Project:
        # Workspace access checks it for people; the service key and auth off skip that. As with
        # workspace access, a deleted workspace still counts.
        if not await self._workspaces.exists_including_deleted(params.workspace_id):
            raise NotFoundError(f"Workspace {params.workspace_id} not found")
        project = Project(
            workspace_id=params.workspace_id, name=params.name, description=params.description
        )
        return await self._repo.create(project)
