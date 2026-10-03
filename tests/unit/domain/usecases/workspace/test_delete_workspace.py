import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.workspace.delete_workspace import DeleteWorkspace, DeleteWorkspaceParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(WorkspaceRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> DeleteWorkspace:
    return DeleteWorkspace(repo)


async def test_should_delete_the_workspace_when_found(
    sut: DeleteWorkspace, repo: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    repo.get_by_id.return_value = Workspace(id=workspace_id, name="W", slug="w")
    await sut.execute(DeleteWorkspaceParams(workspace_id=workspace_id))
    repo.get_by_id.assert_awaited_once_with(workspace_id)
    repo.delete.assert_awaited_once_with(workspace_id)


async def test_should_raise_not_found_error_when_the_workspace_is_missing(
    sut: DeleteWorkspace, repo: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Workspace {workspace_id} not found"):
        await sut.execute(DeleteWorkspaceParams(workspace_id=workspace_id))
    repo.delete.assert_not_awaited()
