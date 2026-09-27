import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.project.delete_project import DeleteProject, DeleteProjectParams


@pytest.fixture
def repo() -> ProjectRepository:
    return cast(ProjectRepository, create_autospec(ProjectRepository))


@pytest.fixture
def sut(repo: ProjectRepository) -> DeleteProject:
    return DeleteProject(repo)


async def test_should_delete_project_when_found(
    sut: DeleteProject, repo: ProjectRepository
) -> None:
    project_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    project = Project(id=project_id, workspace_id=workspace_id, name="My Project")
    repo.get_by_id = AsyncMock(return_value=project)  # type: ignore[method-assign]
    repo.delete = AsyncMock()  # type: ignore[method-assign]
    await sut.execute(DeleteProjectParams(project_id=project_id))
    repo.get_by_id.assert_awaited_once_with(project_id)
    repo.delete.assert_awaited_once_with(project_id)


async def test_should_raise_not_found_error_when_project_missing(
    sut: DeleteProject, repo: ProjectRepository
) -> None:
    project_id = uuid.uuid4()
    repo.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    repo.delete = AsyncMock()  # type: ignore[method-assign]
    with pytest.raises(NotFoundError, match=str(project_id)):
        await sut.execute(DeleteProjectParams(project_id=project_id))
    repo.delete.assert_not_awaited()
