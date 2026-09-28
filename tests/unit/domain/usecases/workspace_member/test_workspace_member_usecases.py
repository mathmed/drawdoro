import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.user_repository import UserRepository
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.user import User
from app.domain.entities.models.workspace import Workspace
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ConflictError, ForbiddenError, NotFoundError
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces, ListWorkspacesParams
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

WORKSPACE_ID = uuid.uuid4()
OWNER_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()


def member(user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(workspace_id=WORKSPACE_ID, user_id=user_id, role=role)


@pytest.fixture
def members() -> WorkspaceMemberRepository:
    mock = cast(WorkspaceMemberRepository, create_autospec(WorkspaceMemberRepository))
    roster = {
        OWNER_ID: member(OWNER_ID, WorkspaceRole.OWNER),
        MEMBER_ID: member(MEMBER_ID, WorkspaceRole.EDITOR),
    }
    mock.get = AsyncMock(side_effect=lambda ws, uid: roster.get(uid))  # type: ignore[method-assign]
    mock.count_owners = AsyncMock(return_value=1)  # type: ignore[method-assign]
    mock.update = AsyncMock(side_effect=lambda m: m)  # type: ignore[method-assign]
    mock.create = AsyncMock(side_effect=lambda m: m)  # type: ignore[method-assign]
    mock.delete = AsyncMock()  # type: ignore[method-assign]
    return mock


@pytest.fixture
def users() -> UserRepository:
    mock = cast(UserRepository, create_autospec(UserRepository))
    mock.get_by_email = AsyncMock(return_value=None)  # type: ignore[method-assign]
    return mock


async def test_should_list_members(members: WorkspaceMemberRepository) -> None:
    details = [
        WorkspaceMemberDetails(
            user_id=OWNER_ID, name="Ana", email="ana@x.com", role=WorkspaceRole.OWNER
        )
    ]
    members.list_details = AsyncMock(return_value=details)  # type: ignore[method-assign]
    sut = ListWorkspaceMembers(members)
    assert await sut.execute(ListWorkspaceMembersParams(workspace_id=WORKSPACE_ID)) == details


async def test_should_add_member_who_already_signed_in(
    members: WorkspaceMemberRepository, users: UserRepository
) -> None:
    newcomer = User(email="bia@x.com", name="Bia")
    users.get_by_email = AsyncMock(return_value=newcomer)  # type: ignore[method-assign]
    sut = AddWorkspaceMember(members, users)
    added = await sut.execute(
        AddWorkspaceMemberParams(
            workspace_id=WORKSPACE_ID, email=" Bia@X.com ", role=WorkspaceRole.VIEWER
        )
    )
    assert (added.email, added.role) == ("bia@x.com", WorkspaceRole.VIEWER)
    users.get_by_email.assert_awaited_once_with("bia@x.com")


async def test_should_reject_unknown_email(
    members: WorkspaceMemberRepository, users: UserRepository
) -> None:
    with pytest.raises(NotFoundError):
        await AddWorkspaceMember(members, users).execute(
            AddWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, email="ghost@x.com", role=WorkspaceRole.EDITOR
            )
        )


async def test_should_reject_duplicate_member(
    members: WorkspaceMemberRepository, users: UserRepository
) -> None:
    users.get_by_email = AsyncMock(return_value=User(id=MEMBER_ID, email="m@x.com", name="M"))  # type: ignore[method-assign]
    with pytest.raises(ConflictError):
        await AddWorkspaceMember(members, users).execute(
            AddWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, email="m@x.com", role=WorkspaceRole.EDITOR
            )
        )


async def test_should_change_role(members: WorkspaceMemberRepository) -> None:
    updated = await UpdateWorkspaceMemberRole(members).execute(
        UpdateWorkspaceMemberRoleParams(
            workspace_id=WORKSPACE_ID, user_id=MEMBER_ID, role=WorkspaceRole.VIEWER
        )
    )
    assert updated.role == WorkspaceRole.VIEWER


async def test_should_keep_the_last_owner(members: WorkspaceMemberRepository) -> None:
    with pytest.raises(ConflictError):
        await UpdateWorkspaceMemberRole(members).execute(
            UpdateWorkspaceMemberRoleParams(
                workspace_id=WORKSPACE_ID, user_id=OWNER_ID, role=WorkspaceRole.EDITOR
            )
        )
    with pytest.raises(ConflictError):
        await RemoveWorkspaceMember(members).execute(
            RemoveWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, user_id=OWNER_ID, acting_user_id=OWNER_ID
            )
        )


async def test_should_report_missing_member(members: WorkspaceMemberRepository) -> None:
    with pytest.raises(NotFoundError):
        await UpdateWorkspaceMemberRole(members).execute(
            UpdateWorkspaceMemberRoleParams(
                workspace_id=WORKSPACE_ID, user_id=uuid.uuid4(), role=WorkspaceRole.VIEWER
            )
        )
    with pytest.raises(NotFoundError):
        await RemoveWorkspaceMember(members).execute(
            RemoveWorkspaceMemberParams(workspace_id=WORKSPACE_ID, user_id=uuid.uuid4())
        )


async def test_should_let_owner_remove_others_and_members_leave(
    members: WorkspaceMemberRepository,
) -> None:
    sut = RemoveWorkspaceMember(members)
    await sut.execute(
        RemoveWorkspaceMemberParams(
            workspace_id=WORKSPACE_ID, user_id=MEMBER_ID, acting_user_id=OWNER_ID
        )
    )
    await sut.execute(
        RemoveWorkspaceMemberParams(
            workspace_id=WORKSPACE_ID, user_id=MEMBER_ID, acting_user_id=MEMBER_ID
        )
    )
    assert members.delete.await_count == 2  # type: ignore[attr-defined]


async def test_should_forbid_non_owners_removing_others(members: WorkspaceMemberRepository) -> None:
    with pytest.raises(ForbiddenError):
        await RemoveWorkspaceMember(members).execute(
            RemoveWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, user_id=OWNER_ID, acting_user_id=MEMBER_ID
            )
        )


async def test_should_list_only_the_users_workspaces(members: WorkspaceMemberRepository) -> None:
    repo = cast(WorkspaceRepository, create_autospec(WorkspaceRepository))
    mine = [Workspace(name="Mine", slug="mine")]
    repo.list_for_user = AsyncMock(return_value=mine)  # type: ignore[method-assign]
    repo.list_without_members = AsyncMock(return_value=[])  # type: ignore[method-assign]
    repo.list_all = AsyncMock(return_value=[])  # type: ignore[method-assign]
    sut = ListWorkspaces(repo, members)
    assert await sut.execute(ListWorkspacesParams(user_id=OWNER_ID)) == mine
    assert await sut.execute(ListWorkspacesParams()) == []
    members.create.assert_not_awaited()  # type: ignore[attr-defined]


async def test_should_give_orphan_workspaces_to_the_first_user_listing(
    members: WorkspaceMemberRepository,
) -> None:
    repo = cast(WorkspaceRepository, create_autospec(WorkspaceRepository))
    orphan = Workspace(name="Legacy", slug="legacy")
    repo.list_without_members = AsyncMock(return_value=[orphan])  # type: ignore[method-assign]
    repo.list_for_user = AsyncMock(return_value=[orphan])  # type: ignore[method-assign]
    await ListWorkspaces(repo, members).execute(ListWorkspacesParams(user_id=OWNER_ID))
    created = members.create.call_args[0][0]  # type: ignore[attr-defined]
    assert (created.workspace_id, created.user_id, created.role) == (
        orphan.id,
        OWNER_ID,
        WorkspaceRole.OWNER,
    )
