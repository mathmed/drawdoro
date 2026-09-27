import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.usecases.workspace.create_workspace import CreateWorkspace, CreateWorkspaceParams


@pytest.fixture
def repo() -> WorkspaceRepository:
    return cast(WorkspaceRepository, create_autospec(WorkspaceRepository))


@pytest.fixture
def sut(repo: WorkspaceRepository) -> CreateWorkspace:
    return CreateWorkspace(repo)


@pytest.fixture
def params() -> CreateWorkspaceParams:
    return CreateWorkspaceParams(name="Acme Corp", slug="acme")


async def test_should_create_workspace_and_return_it(
    sut: CreateWorkspace, repo: WorkspaceRepository, params: CreateWorkspaceParams
) -> None:
    expected = Workspace(name=params.name, slug=params.slug)
    repo.create = AsyncMock(return_value=expected)  # type: ignore[method-assign]
    result = await sut.execute(params)
    assert result.name == params.name
    assert result.slug == params.slug
    repo.create.assert_awaited_once()


async def test_should_generate_uuid_for_new_workspace(
    sut: CreateWorkspace, repo: WorkspaceRepository, params: CreateWorkspaceParams
) -> None:
    workspace_with_id = Workspace(name=params.name, slug=params.slug)
    repo.create = AsyncMock(return_value=workspace_with_id)  # type: ignore[method-assign]
    await sut.execute(params)
    created_arg: Workspace = repo.create.call_args[0][0]
    assert isinstance(created_arg.id, uuid.UUID)
