import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.project.get_project import GetProject, GetProjectParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(ProjectRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> GetProject:
    return GetProject(repo)


async def test_should_return_the_project_when_found(
    sut: GetProject, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    expected = Project(id=project_id, workspace_id=uuid.uuid4(), name="P")
    repo.get_by_id.return_value = expected
    assert await sut.execute(GetProjectParams(project_id=project_id)) is expected
    repo.get_by_id.assert_awaited_once_with(project_id)


async def test_should_raise_not_found_error_when_the_project_is_missing(
    sut: GetProject, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Project {project_id} not found"):
        await sut.execute(GetProjectParams(project_id=project_id))
