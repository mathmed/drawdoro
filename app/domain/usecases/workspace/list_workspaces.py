import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.workspace_role import WorkspaceRole


class ListWorkspacesParams(InputData):
    # Only the user's workspaces; None (authentication disabled) lists every workspace.
    user_id: uuid.UUID | None = None


class ListWorkspaces(Usecase[ListWorkspacesParams, list[Workspace]]):
    def __init__(self, repo: WorkspaceRepository, members: WorkspaceMemberRepository) -> None:
        self._repo = repo
        self._members = members

    async def execute(self, params: ListWorkspacesParams) -> list[Workspace]:
        if params.user_id is None:
            return await self._repo.list_all()
        await self._adopt_orphans(params.user_id)
        return await self._repo.list_for_user(params.user_id)

    # Workspaces created before memberships existed have no members, so nobody could reach
    # them; the first signed-in user to list workspaces becomes their owner.
    async def _adopt_orphans(self, user_id: uuid.UUID) -> None:
        for workspace in await self._repo.list_without_members():
            await self._members.create(
                WorkspaceMember(
                    workspace_id=workspace.id, user_id=user_id, role=WorkspaceRole.OWNER
                )
            )
