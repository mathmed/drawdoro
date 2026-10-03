import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock, NonCallableMagicMock

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
from tests.doubles import double

WORKSPACE_ID = uuid.uuid4()
OWNER_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()
APP_NAME = "Acme Draw"
LAST_OWNER = "A workspace needs at least one owner"


def member(user_id: uuid.UUID, role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(workspace_id=WORKSPACE_ID, user_id=user_id, role=role)


@pytest.fixture
def members() -> NonCallableMagicMock:
    mock = double(WorkspaceMemberRepository)
    roster = {
        OWNER_ID: member(OWNER_ID, WorkspaceRole.OWNER),
        MEMBER_ID: member(MEMBER_ID, WorkspaceRole.EDITOR),
    }
    mock.get.side_effect = lambda ws, uid: roster.get(uid) if ws == WORKSPACE_ID else None
    mock.count_owners.return_value = 1
    mock.update.side_effect = lambda m: m
    mock.create.side_effect = lambda m: m
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def users() -> NonCallableMagicMock:
    mock = double(UserRepository)
    mock.get_by_email.return_value = None
    return mock


async def test_should_list_members(members: NonCallableMagicMock) -> None:
    details = [
        WorkspaceMemberDetails(
            user_id=OWNER_ID, name="Ana", email="ana@x.com", role=WorkspaceRole.OWNER
        )
    ]
    members.list_details.return_value = details
    sut = ListWorkspaceMembers(members)
    assert await sut.execute(ListWorkspaceMembersParams(workspace_id=WORKSPACE_ID)) == details
    members.list_details.assert_awaited_once_with(WORKSPACE_ID)


async def test_should_add_member_who_already_signed_in(
    members: NonCallableMagicMock, users: NonCallableMagicMock
) -> None:
    newcomer = User(email="bia@x.com", name="Bia")
    users.get_by_email.return_value = newcomer
    sut = AddWorkspaceMember(members, users, APP_NAME)
    added = await sut.execute(
        AddWorkspaceMemberParams(
            workspace_id=WORKSPACE_ID, email=" Bia@X.com ", role=WorkspaceRole.EDITOR
        )
    )
    assert (added.email, added.role) == ("bia@x.com", WorkspaceRole.EDITOR)
    users.get_by_email.assert_awaited_once_with("bia@x.com")
    created = members.create.call_args.args[0]
    assert (created.workspace_id, created.user_id, created.role) == (
        WORKSPACE_ID,
        newcomer.id,
        WorkspaceRole.EDITOR,
    )


async def test_should_reject_unknown_email(
    members: NonCallableMagicMock, users: NonCallableMagicMock
) -> None:
    with pytest.raises(NotFoundError, match="ghost@x.com hasn't signed in to Acme Draw yet"):
        await AddWorkspaceMember(members, users, APP_NAME).execute(
            AddWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, email="ghost@x.com", role=WorkspaceRole.EDITOR
            )
        )


async def test_should_reject_duplicate_member(
    members: NonCallableMagicMock, users: NonCallableMagicMock
) -> None:
    users.get_by_email.return_value = User(id=MEMBER_ID, email="m@x.com", name="M")
    with pytest.raises(ConflictError, match="^m@x.com is already a member of this workspace$"):
        await AddWorkspaceMember(members, users, APP_NAME).execute(
            AddWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, email="m@x.com", role=WorkspaceRole.EDITOR
            )
        )


async def test_should_change_role(members: NonCallableMagicMock) -> None:
    updated = await UpdateWorkspaceMemberRole(members).execute(
        UpdateWorkspaceMemberRoleParams(
            workspace_id=WORKSPACE_ID, user_id=MEMBER_ID, role=WorkspaceRole.VIEWER
        )
    )
    assert updated.role == WorkspaceRole.VIEWER


async def test_should_keep_the_last_owner(members: NonCallableMagicMock) -> None:
    with pytest.raises(ConflictError, match=f"^{LAST_OWNER}$"):
        await UpdateWorkspaceMemberRole(members).execute(
            UpdateWorkspaceMemberRoleParams(
                workspace_id=WORKSPACE_ID, user_id=OWNER_ID, role=WorkspaceRole.EDITOR
            )
        )
    with pytest.raises(ConflictError, match=f"^{LAST_OWNER}$"):
        await RemoveWorkspaceMember(members).execute(
            RemoveWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, user_id=OWNER_ID, acting_user_id=OWNER_ID
            )
        )


async def test_should_report_missing_member(members: NonCallableMagicMock) -> None:
    with pytest.raises(NotFoundError, match="^Member not found$"):
        await UpdateWorkspaceMemberRole(members).execute(
            UpdateWorkspaceMemberRoleParams(
                workspace_id=WORKSPACE_ID, user_id=uuid.uuid4(), role=WorkspaceRole.VIEWER
            )
        )
    with pytest.raises(NotFoundError, match="^Member not found$"):
        await RemoveWorkspaceMember(members).execute(
            RemoveWorkspaceMemberParams(workspace_id=WORKSPACE_ID, user_id=uuid.uuid4())
        )


async def test_should_let_owner_remove_others_and_members_leave(
    members: NonCallableMagicMock,
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
    assert members.delete.await_count == 2


async def test_should_forbid_non_owners_removing_others(members: NonCallableMagicMock) -> None:
    with pytest.raises(ForbiddenError, match="^Only owners can remove other members$"):
        await RemoveWorkspaceMember(members).execute(
            RemoveWorkspaceMemberParams(
                workspace_id=WORKSPACE_ID, user_id=OWNER_ID, acting_user_id=MEMBER_ID
            )
        )


async def test_should_list_only_the_users_workspaces(members: NonCallableMagicMock) -> None:
    repo = double(WorkspaceRepository)
    mine = [Workspace(name="Mine", slug="mine")]
    repo.list_for_user.return_value = mine
    repo.list_without_members.return_value = []
    repo.list_all.return_value = []
    sut = ListWorkspaces(repo, members)
    assert await sut.execute(ListWorkspacesParams(user_id=OWNER_ID)) == mine
    repo.list_for_user.assert_awaited_once_with(OWNER_ID)
    assert await sut.execute(ListWorkspacesParams()) == []
    members.create.assert_not_awaited()


async def test_should_give_orphan_workspaces_to_the_first_user_listing(
    members: NonCallableMagicMock,
) -> None:
    repo = double(WorkspaceRepository)
    orphan = Workspace(name="Legacy", slug="legacy")
    repo.list_without_members.return_value = [orphan]
    repo.list_for_user.return_value = [orphan]
    await ListWorkspaces(repo, members).execute(ListWorkspacesParams(user_id=OWNER_ID))
    created = members.create.call_args[0][0]
    assert (created.workspace_id, created.user_id, created.role) == (
        orphan.id,
        OWNER_ID,
        WorkspaceRole.OWNER,
    )


def owners_count(count: int) -> Callable[[uuid.UUID], int]:
    return lambda workspace_id: count if workspace_id == WORKSPACE_ID else 0


async def test_should_demote_an_owner_when_another_owner_remains(
    members: NonCallableMagicMock,
) -> None:
    members.count_owners.side_effect = owners_count(2)
    updated = await UpdateWorkspaceMemberRole(members).execute(
        UpdateWorkspaceMemberRoleParams(
            workspace_id=WORKSPACE_ID, user_id=OWNER_ID, role=WorkspaceRole.EDITOR
        )
    )
    assert (updated.user_id, updated.role) == (OWNER_ID, WorkspaceRole.EDITOR)
    members.update.assert_awaited_once_with(updated)


async def test_should_remove_an_owner_when_another_owner_remains(
    members: NonCallableMagicMock,
) -> None:
    members.count_owners.side_effect = owners_count(2)
    await RemoveWorkspaceMember(members).execute(
        RemoveWorkspaceMemberParams(
            workspace_id=WORKSPACE_ID, user_id=OWNER_ID, acting_user_id=OWNER_ID
        )
    )
    owner = await members.get(WORKSPACE_ID, OWNER_ID)
    members.delete.assert_awaited_once_with(owner.id)


async def test_should_delete_the_removed_member_record(members: NonCallableMagicMock) -> None:
    removed = await members.get(WORKSPACE_ID, MEMBER_ID)
    await RemoveWorkspaceMember(members).execute(
        RemoveWorkspaceMemberParams(workspace_id=WORKSPACE_ID, user_id=MEMBER_ID)
    )
    members.delete.assert_awaited_once_with(removed.id)
