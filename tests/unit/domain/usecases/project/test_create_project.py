import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.project.create_project import CreateProject, CreateProjectParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    mock = double(ProjectRepository)
    mock.create.side_effect = lambda project: project
    return mock


@pytest.fixture
def workspaces() -> NonCallableMagicMock:
    mock = double(WorkspaceRepository)
    mock.exists_including_deleted.return_value = True
    return mock


@pytest.fixture
def sut(repo: NonCallableMagicMock, workspaces: NonCallableMagicMock) -> CreateProject:
    return CreateProject(repo, workspaces)


async def test_should_store_the_project_in_its_workspace(
    sut: CreateProject, repo: NonCallableMagicMock, workspaces: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    created = await sut.execute(
        CreateProjectParams(workspace_id=workspace_id, name="Core", description="Payments")
    )
    assert (created.workspace_id, created.name, created.description) == (
        workspace_id,
        "Core",
        "Payments",
    )
    workspaces.exists_including_deleted.assert_awaited_once_with(workspace_id)
    repo.create.assert_awaited_once_with(created)


async def test_should_default_to_an_empty_description(sut: CreateProject) -> None:
    created = await sut.execute(CreateProjectParams(workspace_id=uuid.uuid4(), name="Core"))
    assert isinstance(created, Project)
    assert created.description == ""


async def test_should_raise_not_found_error_when_the_workspace_does_not_exist(
    sut: CreateProject, repo: NonCallableMagicMock, workspaces: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    workspaces.exists_including_deleted.return_value = False
    with pytest.raises(NotFoundError, match=f"^Workspace {workspace_id} not found$"):
        await sut.execute(CreateProjectParams(workspace_id=workspace_id, name="Core"))
    repo.create.assert_not_awaited()
