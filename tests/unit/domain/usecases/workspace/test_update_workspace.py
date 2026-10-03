import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.workspace.update_workspace import UpdateWorkspace, UpdateWorkspaceParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(WorkspaceRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> UpdateWorkspace:
    return UpdateWorkspace(repo)


async def test_should_update_the_workspace_when_found(
    sut: UpdateWorkspace, repo: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    repo.get_by_id.return_value = Workspace(id=workspace_id, name="Old", slug="old")
    repo.update.side_effect = lambda workspace: workspace
    result = await sut.execute(
        UpdateWorkspaceParams(workspace_id=workspace_id, name="New", slug="new")
    )
    repo.get_by_id.assert_awaited_once_with(workspace_id)
    updated = repo.update.await_args.args[0]
    assert result is updated
    assert updated.id == workspace_id
    assert updated.name == "New"
    assert updated.slug == "new"


async def test_should_raise_not_found_error_when_the_workspace_is_missing(
    sut: UpdateWorkspace, repo: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Workspace {workspace_id} not found"):
        await sut.execute(UpdateWorkspaceParams(workspace_id=workspace_id, name="New", slug="new"))
    repo.update.assert_not_awaited()
