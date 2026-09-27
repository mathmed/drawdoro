import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import NotFoundError


class GetWorkspaceParams(InputData):
    workspace_id: uuid.UUID


class GetWorkspace(Usecase[GetWorkspaceParams, Workspace]):
    def __init__(self, repo: WorkspaceRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetWorkspaceParams) -> Workspace:
        workspace = await self._repo.get_by_id(params.workspace_id)
        if workspace is None:
            raise NotFoundError(f"Workspace {params.workspace_id} not found")
        return workspace
