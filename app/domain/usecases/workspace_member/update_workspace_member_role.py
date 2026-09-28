import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ConflictError, NotFoundError


class UpdateWorkspaceMemberRoleParams(InputData):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole


class UpdateWorkspaceMemberRole(Usecase[UpdateWorkspaceMemberRoleParams, WorkspaceMember]):
    def __init__(self, members: WorkspaceMemberRepository) -> None:
        self._members = members

    async def execute(self, params: UpdateWorkspaceMemberRoleParams) -> WorkspaceMember:
        member = await self._members.get(params.workspace_id, params.user_id)
        if member is None:
            raise NotFoundError("Member not found")
        is_demotion = member.role == WorkspaceRole.OWNER and params.role != WorkspaceRole.OWNER
        if is_demotion and await self._members.count_owners(params.workspace_id) <= 1:
            raise ConflictError("A workspace needs at least one owner")
        member.role = params.role
        return await self._members.update(member)
