import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.workspace_role import WorkspaceRole


class CreateWorkspaceParams(InputData):
    name: str
    slug: str
    # The creator becomes the owner; None when authentication is disabled.
    creator_id: uuid.UUID | None = None


class CreateWorkspace(Usecase[CreateWorkspaceParams, Workspace]):
    def __init__(self, repo: WorkspaceRepository, members: WorkspaceMemberRepository) -> None:
        self._repo = repo
        self._members = members

    async def execute(self, params: CreateWorkspaceParams) -> Workspace:
        workspace = await self._repo.create(Workspace(name=params.name, slug=params.slug))
        if params.creator_id is not None:
            await self._members.create(
                WorkspaceMember(
                    workspace_id=workspace.id, user_id=params.creator_id, role=WorkspaceRole.OWNER
                )
            )
        return workspace
