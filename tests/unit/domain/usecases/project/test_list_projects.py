import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.project import Project
from app.domain.usecases.project.list_projects import ListProjects, ListProjectsParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(ProjectRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ListProjects:
    return ListProjects(repo)


async def test_should_list_the_projects_of_the_workspace(
    sut: ListProjects, repo: NonCallableMagicMock
) -> None:
    workspace_id = uuid.uuid4()
    projects = [Project(workspace_id=workspace_id, name="Core")]
    repo.list_by_workspace.return_value = projects
    assert await sut.execute(ListProjectsParams(workspace_id=workspace_id)) == projects
    repo.list_by_workspace.assert_awaited_once_with(workspace_id)
