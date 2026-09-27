from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace


class CreateWorkspaceParams(InputData):
    name: str
    slug: str


class CreateWorkspace(Usecase[CreateWorkspaceParams, Workspace]):
    def __init__(self, repo: WorkspaceRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateWorkspaceParams) -> Workspace:
        workspace = Workspace(name=params.name, slug=params.slug)
        return await self._repo.create(workspace)
