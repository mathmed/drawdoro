import uuid
from unittest.mock import AsyncMock, NonCallableMagicMock

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.project.delete_project import DeleteProject, DeleteProjectParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(ProjectRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> DeleteProject:
    return DeleteProject(repo)


async def test_should_delete_project_when_found(
    sut: DeleteProject, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    project = Project(id=project_id, workspace_id=workspace_id, name="My Project")
    repo.get_by_id.return_value = project
    repo.delete = AsyncMock()
    await sut.execute(DeleteProjectParams(project_id=project_id))
    repo.get_by_id.assert_awaited_once_with(project_id)
    repo.delete.assert_awaited_once_with(project_id)


async def test_should_raise_not_found_error_when_project_missing(
    sut: DeleteProject, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    repo.delete = AsyncMock()
    with pytest.raises(NotFoundError, match=str(project_id)):
        await sut.execute(DeleteProjectParams(project_id=project_id))
    repo.delete.assert_not_awaited()
