import uuid

from fastapi import APIRouter, Depends

from app.domain.entities.models.user import User
from app.domain.usecases.workspace_member.add_workspace_member import (
    AddWorkspaceMember,
    AddWorkspaceMemberParams,
)
from app.domain.usecases.workspace_member.list_workspace_members import (
    ListWorkspaceMembers,
    ListWorkspaceMembersParams,
)
from app.domain.usecases.workspace_member.remove_workspace_member import (
    RemoveWorkspaceMember,
    RemoveWorkspaceMemberParams,
)
from app.domain.usecases.workspace_member.update_workspace_member_role import (
    UpdateWorkspaceMemberRole,
    UpdateWorkspaceMemberRoleParams,
)
from app.presentation.factories.workspace_member_factories import (
    add_workspace_member_factory,
    list_workspace_members_factory,
    remove_workspace_member_factory,
    update_workspace_member_role_factory,
)
from app.presentation.fastapi.dependencies.current_user import get_current_user
from app.presentation.fastapi.dependencies.workspace_access import (
    require_workspace_member,
    require_workspace_owner,
)
from app.presentation.fastapi.schemas.workspace_member_schemas import (
    AddWorkspaceMemberRequest,
    UpdateWorkspaceMemberRoleRequest,
    WorkspaceMemberResponse,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/members", tags=["workspace members"])


@router.get(
    "",
    response_model=list[WorkspaceMemberResponse],
    dependencies=[Depends(require_workspace_member)],
)
async def list_members(
    workspace_id: uuid.UUID,
    use_case: ListWorkspaceMembers = Depends(list_workspace_members_factory),
) -> list[WorkspaceMemberResponse]:
    members = await use_case.execute(ListWorkspaceMembersParams(workspace_id=workspace_id))
    return [WorkspaceMemberResponse.model_validate(m) for m in members]


@router.post(
    "",
    response_model=WorkspaceMemberResponse,
    status_code=201,
    dependencies=[Depends(require_workspace_owner)],
)
async def add_member(
    workspace_id: uuid.UUID,
    body: AddWorkspaceMemberRequest,
    use_case: AddWorkspaceMember = Depends(add_workspace_member_factory),
) -> WorkspaceMemberResponse:
    member = await use_case.execute(
        AddWorkspaceMemberParams(workspace_id=workspace_id, email=body.email, role=body.role)
    )
    return WorkspaceMemberResponse.model_validate(member)


@router.put("/{user_id}", status_code=204, dependencies=[Depends(require_workspace_owner)])
async def update_member_role(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    body: UpdateWorkspaceMemberRoleRequest,
    use_case: UpdateWorkspaceMemberRole = Depends(update_workspace_member_role_factory),
) -> None:
    await use_case.execute(
        UpdateWorkspaceMemberRoleParams(workspace_id=workspace_id, user_id=user_id, role=body.role)
    )


@router.delete("/{user_id}", status_code=204, dependencies=[Depends(require_workspace_member)])
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    user: User | None = Depends(get_current_user),
    use_case: RemoveWorkspaceMember = Depends(remove_workspace_member_factory),
) -> None:
    await use_case.execute(
        RemoveWorkspaceMemberParams(
            workspace_id=workspace_id,
            user_id=user_id,
            acting_user_id=user.id if user is not None else None,
        )
    )
