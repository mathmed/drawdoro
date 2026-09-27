from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace


class ListWorkspacesParams(InputData):
    pass


class ListWorkspaces(Usecase[ListWorkspacesParams, list[Workspace]]):
    def __init__(self, repo: WorkspaceRepository) -> None:
        self._repo = repo

    async def execute(self, params: ListWorkspacesParams) -> list[Workspace]:
        return await self._repo.list_all()
