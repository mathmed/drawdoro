import uuid
from unittest.mock import AsyncMock, NonCallableMagicMock

import pytest

from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.usecases.workspace.create_workspace import CreateWorkspace, CreateWorkspaceParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(WorkspaceRepository)


@pytest.fixture
def members() -> NonCallableMagicMock:
    return double(WorkspaceMemberRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock, members: NonCallableMagicMock) -> CreateWorkspace:
    return CreateWorkspace(repo, members)


@pytest.fixture
def params() -> CreateWorkspaceParams:
    return CreateWorkspaceParams(name="Acme Corp", slug="acme")


async def test_should_create_workspace_and_return_it(
    sut: CreateWorkspace, repo: NonCallableMagicMock, params: CreateWorkspaceParams
) -> None:
    expected = Workspace(name=params.name, slug=params.slug)
    repo.create.return_value = expected
    result = await sut.execute(params)
    assert result.name == params.name
    assert result.slug == params.slug
    repo.create.assert_awaited_once()


async def test_should_generate_uuid_for_new_workspace(
    sut: CreateWorkspace, repo: NonCallableMagicMock, params: CreateWorkspaceParams
) -> None:
    workspace_with_id = Workspace(name=params.name, slug=params.slug)
    repo.create.return_value = workspace_with_id
    await sut.execute(params)
    created_arg: Workspace = repo.create.call_args[0][0]
    assert isinstance(created_arg.id, uuid.UUID)


async def test_should_make_creator_the_owner(
    sut: CreateWorkspace, repo: NonCallableMagicMock, members: NonCallableMagicMock
) -> None:
    workspace = Workspace(name="Acme Corp", slug="acme")
    creator_id = uuid.uuid4()
    repo.create.return_value = workspace
    members.create = AsyncMock()
    await sut.execute(CreateWorkspaceParams(name="Acme Corp", slug="acme", creator_id=creator_id))
    member = members.create.call_args[0][0]
    assert (member.workspace_id, member.user_id, member.role) == (
        workspace.id,
        creator_id,
        WorkspaceRole.OWNER,
    )


async def test_should_not_add_member_without_creator(
    sut: CreateWorkspace,
    repo: NonCallableMagicMock,
    members: NonCallableMagicMock,
    params: CreateWorkspaceParams,
) -> None:
    repo.create.return_value = Workspace(name="Acme Corp", slug="acme")
    members.create = AsyncMock()
    await sut.execute(params)
    members.create.assert_not_awaited()
