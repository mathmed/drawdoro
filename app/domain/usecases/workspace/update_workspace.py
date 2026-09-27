import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import NotFoundError


class UpdateWorkspaceParams(InputData):
    workspace_id: uuid.UUID
    name: str
    slug: str


class UpdateWorkspace(Usecase[UpdateWorkspaceParams, Workspace]):
    def __init__(self, repo: WorkspaceRepository) -> None:
        self._repo = repo

    async def execute(self, params: UpdateWorkspaceParams) -> Workspace:
        workspace = await self._repo.get_by_id(params.workspace_id)
        if workspace is None:
            raise NotFoundError(f"Workspace {params.workspace_id} not found")
        workspace.name = params.name
        workspace.slug = params.slug
        return await self._repo.update(workspace)
