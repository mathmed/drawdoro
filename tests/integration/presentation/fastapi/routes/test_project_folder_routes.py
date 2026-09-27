import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.folder.create_folder import CreateFolder
from app.domain.usecases.folder.delete_folder import DeleteFolder
from app.domain.usecases.folder.get_folder import GetFolder
from app.domain.usecases.folder.update_folder import UpdateFolder
from app.domain.usecases.project.create_project import CreateProject
from app.domain.usecases.project.delete_project import DeleteProject
from app.domain.usecases.project.get_project import GetProject
from app.domain.usecases.project.update_project import UpdateProject
from app.main.main import app
from app.presentation.factories.folder_factories import (
    create_folder_factory,
    delete_folder_factory,
    get_folder_factory,
    update_folder_factory,
)
from app.presentation.factories.project_factories import (
    create_project_factory,
    delete_project_factory,
    get_project_factory,
    update_project_factory,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_create_project(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    project = Project(workspace_id=workspace_id, name="Proj")
    mock_uc = AsyncMock(spec=CreateProject)
    mock_uc.execute.return_value = project
    app.dependency_overrides[create_project_factory] = lambda: mock_uc
    try:
        response = client.post(f"/workspaces/{workspace_id}/projects", json={"name": "Proj"})
        assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_should_get_project(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    project = Project(workspace_id=workspace_id, name="Proj")
    mock_uc = AsyncMock(spec=GetProject)
    mock_uc.execute.return_value = project
    app.dependency_overrides[get_project_factory] = lambda: mock_uc
    try:
        response = client.get(f"/workspaces/{workspace_id}/projects/{project.id}")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_when_project_not_found(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    pid = uuid.uuid4()
    mock_uc = AsyncMock(spec=GetProject)
    mock_uc.execute.side_effect = NotFoundError(f"Project {pid} not found")
    app.dependency_overrides[get_project_factory] = lambda: mock_uc
    try:
        response = client.get(f"/workspaces/{workspace_id}/projects/{pid}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_should_update_project(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    project = Project(workspace_id=workspace_id, name="Updated")
    mock_uc = AsyncMock(spec=UpdateProject)
    mock_uc.execute.return_value = project
    app.dependency_overrides[update_project_factory] = lambda: mock_uc
    try:
        response = client.put(
            f"/workspaces/{workspace_id}/projects/{project.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_delete_project(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    pid = uuid.uuid4()
    mock_uc = AsyncMock(spec=DeleteProject)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_project_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/workspaces/{workspace_id}/projects/{pid}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_should_create_folder(client: TestClient) -> None:
    project_id = uuid.uuid4()
    folder = Folder(project_id=project_id, name="F")
    mock_uc = AsyncMock(spec=CreateFolder)
    mock_uc.execute.return_value = folder
    app.dependency_overrides[create_folder_factory] = lambda: mock_uc
    try:
        response = client.post(f"/projects/{project_id}/folders", json={"name": "F"})
        assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_should_get_folder(client: TestClient) -> None:
    project_id = uuid.uuid4()
    folder = Folder(project_id=project_id, name="F")
    mock_uc = AsyncMock(spec=GetFolder)
    mock_uc.execute.return_value = folder
    app.dependency_overrides[get_folder_factory] = lambda: mock_uc
    try:
        response = client.get(f"/projects/{project_id}/folders/{folder.id}")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_update_folder(client: TestClient) -> None:
    project_id = uuid.uuid4()
    folder = Folder(project_id=project_id, name="Updated")
    mock_uc = AsyncMock(spec=UpdateFolder)
    mock_uc.execute.return_value = folder
    app.dependency_overrides[update_folder_factory] = lambda: mock_uc
    try:
        response = client.put(
            f"/projects/{project_id}/folders/{folder.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_delete_folder(client: TestClient) -> None:
    project_id = uuid.uuid4()
    fid = uuid.uuid4()
    mock_uc = AsyncMock(spec=DeleteFolder)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_folder_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/projects/{project_id}/folders/{fid}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
