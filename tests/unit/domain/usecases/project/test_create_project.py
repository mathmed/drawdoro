import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.domain.usecases.project.create_project import CreateProject, CreateProjectParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    mock = double(ProjectRepository)
    mock.create.side_effect = lambda project: project
    return mock


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> CreateProject:
    return CreateProject(repo)


async def test_should_store_the_project_in_its_workspace(
    sut: CreateProject, repo: NonCallableMagicMock
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
    repo.create.assert_awaited_once_with(created)


async def test_should_default_to_an_empty_description(sut: CreateProject) -> None:
    created = await sut.execute(CreateProjectParams(workspace_id=uuid.uuid4(), name="Core"))
    assert isinstance(created, Project)
    assert created.description == ""
