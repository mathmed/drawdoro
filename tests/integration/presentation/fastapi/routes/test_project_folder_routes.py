import uuid
from unittest.mock import AsyncMock, NonCallableMagicMock

import pytest
from fastapi.testclient import TestClient

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.project_placement import ProjectPlacement
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
from tests.doubles import double


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


# Authentication is off in the tests, so nothing checks the path's project before the use case:
# the path a trusted service (the MCP server) takes.
@pytest.fixture
def projects() -> NonCallableMagicMock:
    return double(ProjectRepository)


@pytest.fixture
def folders() -> NonCallableMagicMock:
    repo = double(FolderRepository)
    repo.get_by_id.return_value = None
    repo.update.side_effect = lambda folder: folder
    return repo


def existing_project(projects: NonCallableMagicMock) -> uuid.UUID:
    project = Project(workspace_id=uuid.uuid4(), name="Shop")
    projects.get_by_id.return_value = project
    return project.id


def test_should_return_404_when_creating_a_folder_in_a_missing_project(
    client: TestClient, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    projects.get_by_id.return_value = None
    placement = ProjectPlacement(projects, folders)
    app.dependency_overrides[create_folder_factory] = lambda: CreateFolder(folders, placement)
    try:
        response = client.post(f"/projects/{project_id}/folders", json={"name": "F"})
        assert response.status_code == 404
        assert response.json() == {"detail": f"Project {project_id} not found"}
        folders.create.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_when_creating_a_folder_under_a_missing_parent(
    client: TestClient, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    project_id = existing_project(projects)
    parent_id = uuid.uuid4()
    placement = ProjectPlacement(projects, folders)
    app.dependency_overrides[create_folder_factory] = lambda: CreateFolder(folders, placement)
    try:
        response = client.post(
            f"/projects/{project_id}/folders",
            json={"name": "F", "parent_folder_id": str(parent_id)},
        )
        assert response.status_code == 404
        assert response.json() == {"detail": f"Folder {parent_id} not found"}
        folders.create.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_when_moving_a_folder_under_a_missing_parent(
    client: TestClient, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    folder = Folder(project_id=existing_project(projects), name="F")
    parent_id = uuid.uuid4()
    folders.get_by_id.side_effect = lambda folder_id: folder if folder_id == folder.id else None
    placement = ProjectPlacement(projects, folders)
    app.dependency_overrides[update_folder_factory] = lambda: UpdateFolder(folders, placement)
    try:
        response = client.put(
            f"/projects/{folder.project_id}/folders/{folder.id}",
            json={"name": "F", "parent_folder_id": str(parent_id)},
        )
        assert response.status_code == 404
        assert response.json() == {"detail": f"Folder {parent_id} not found"}
        folders.update.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()


def test_should_keep_renaming_a_folder_whose_parent_was_deleted(
    client: TestClient, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    deleted_parent_id = uuid.uuid4()
    folder = Folder(
        project_id=existing_project(projects), parent_folder_id=deleted_parent_id, name="F"
    )
    folders.get_by_id.side_effect = lambda folder_id: folder if folder_id == folder.id else None
    placement = ProjectPlacement(projects, folders)
    app.dependency_overrides[update_folder_factory] = lambda: UpdateFolder(folders, placement)
    try:
        response = client.put(
            f"/projects/{folder.project_id}/folders/{folder.id}",
            json={"name": "Renamed", "parent_folder_id": str(deleted_parent_id)},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/projects/{project_id}/folders", "post"),
        ("/projects/{project_id}/folders/{folder_id}", "put"),
    ],
)
def test_should_document_the_missing_project_or_folder(path: str, method: str) -> None:
    not_found = app.openapi()["paths"][path][method]["responses"]["404"]
    assert not_found["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
