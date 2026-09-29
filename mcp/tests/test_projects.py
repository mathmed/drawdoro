import uuid
from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import BackendApi
from tools.projects import ProjectTools


@pytest.fixture
def api() -> MagicMock:
    return cast(MagicMock, create_autospec(BackendApi, instance=True))


@pytest.fixture
def sut(api: MagicMock) -> ProjectTools:
    return ProjectTools(api)


def test_should_list_projects_of_workspace(sut: ProjectTools, api: MagicMock) -> None:
    workspace_id = uuid.uuid4()
    api.get_list.return_value = [{"id": "p1"}]
    assert sut.list_projects(workspace_id) == [{"id": "p1"}]
    api.get_list.assert_called_once_with(f"/workspaces/{workspace_id}/projects")


def test_should_get_project_of_workspace(sut: ProjectTools, api: MagicMock) -> None:
    workspace_id, project_id = uuid.uuid4(), uuid.uuid4()
    api.get_object.return_value = {"id": str(project_id)}
    assert sut.get_project(workspace_id, project_id) == {"id": str(project_id)}
    api.get_object.assert_called_once_with(f"/workspaces/{workspace_id}/projects/{project_id}")


def test_should_create_project_in_workspace(sut: ProjectTools, api: MagicMock) -> None:
    workspace_id = uuid.uuid4()
    api.post.return_value = {"id": "p1"}
    assert sut.create_project(workspace_id, "Payments") == {"id": "p1"}
    api.post.assert_called_once_with(
        f"/workspaces/{workspace_id}/projects", {"name": "Payments", "description": ""}
    )
