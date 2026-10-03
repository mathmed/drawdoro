import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.project.update_project import UpdateProject, UpdateProjectParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(ProjectRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> UpdateProject:
    return UpdateProject(repo)


async def test_should_update_the_project_when_found(
    sut: UpdateProject, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    repo.get_by_id.return_value = Project(
        id=project_id, workspace_id=uuid.uuid4(), name="Old", description="old"
    )
    repo.update.side_effect = lambda project: project
    result = await sut.execute(
        UpdateProjectParams(project_id=project_id, name="New", description="new")
    )
    repo.get_by_id.assert_awaited_once_with(project_id)
    updated = repo.update.await_args.args[0]
    assert result is updated
    assert updated.id == project_id
    assert updated.name == "New"
    assert updated.description == "new"


async def test_should_raise_not_found_error_when_the_project_is_missing(
    sut: UpdateProject, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Project {project_id} not found"):
        await sut.execute(UpdateProjectParams(project_id=project_id, name="New", description="new"))
    repo.update.assert_not_awaited()
