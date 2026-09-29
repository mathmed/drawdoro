import uuid

from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.user_repository import UserRepository
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ConflictError, NotFoundError


class AddWorkspaceMemberParams(InputData):
    workspace_id: uuid.UUID
    email: str
    role: WorkspaceRole


class AddWorkspaceMember(Usecase[AddWorkspaceMemberParams, WorkspaceMemberDetails]):
    def __init__(
        self, members: WorkspaceMemberRepository, users: UserRepository, app_name: str
    ) -> None:
        self._members = members
        self._users = users
        self._app_name = app_name

    async def execute(self, params: AddWorkspaceMemberParams) -> WorkspaceMemberDetails:
        # Users only exist after their first sign-in, so invitations need that to happen first.
        user = await self._users.get_by_email(params.email.strip().lower())
        if user is None:
            raise NotFoundError(f"{params.email} hasn't signed in to {self._app_name} yet")
        if await self._members.get(params.workspace_id, user.id) is not None:
            raise ConflictError(f"{params.email} is already a member of this workspace")
        await self._members.create(
            WorkspaceMember(workspace_id=params.workspace_id, user_id=user.id, role=params.role)
        )
        return WorkspaceMemberDetails(
            user_id=user.id, name=user.name, email=user.email, role=params.role
        )
