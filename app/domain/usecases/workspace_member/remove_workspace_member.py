import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ConflictError, ForbiddenError, NotFoundError


class RemoveWorkspaceMemberParams(InputData):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    # None when authentication is disabled or a trusted service calls.
    acting_user_id: uuid.UUID | None = None


class RemoveWorkspaceMember(Usecase[RemoveWorkspaceMemberParams, None]):
    def __init__(self, members: WorkspaceMemberRepository) -> None:
        self._members = members

    async def execute(self, params: RemoveWorkspaceMemberParams) -> None:
        member = await self._members.get(params.workspace_id, params.user_id)
        if member is None:
            raise NotFoundError("Member not found")
        await self._ensure_allowed(params)
        if (
            member.role == WorkspaceRole.OWNER
            and await self._members.count_owners(params.workspace_id) <= 1
        ):
            raise ConflictError("A workspace needs at least one owner")
        await self._members.delete(member.id)

    # Owners manage everyone; any member may leave on their own.
    async def _ensure_allowed(self, params: RemoveWorkspaceMemberParams) -> None:
        if params.acting_user_id is None or params.acting_user_id == params.user_id:
            return
        acting = await self._members.get(params.workspace_id, params.acting_user_id)
        if acting is None or acting.role != WorkspaceRole.OWNER:
            raise ForbiddenError("Only owners can remove other members")
