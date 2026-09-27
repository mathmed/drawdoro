import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.errors.domain_errors import NotFoundError


class DeleteWorkspaceParams(InputData):
    workspace_id: uuid.UUID


class DeleteWorkspace(Usecase[DeleteWorkspaceParams, None]):
    def __init__(self, repo: WorkspaceRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteWorkspaceParams) -> None:
        workspace = await self._repo.get_by_id(params.workspace_id)
        if workspace is None:
            raise NotFoundError(f"Workspace {params.workspace_id} not found")
        await self._repo.delete(params.workspace_id)
