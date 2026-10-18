import uuid
from collections.abc import Callable
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import ConflictError, NotFoundError
from app.domain.usecases.workspace.create_workspace import CreateWorkspace
from app.domain.usecases.workspace.delete_workspace import DeleteWorkspace
from app.domain.usecases.workspace.get_workspace import GetWorkspace
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces
from app.domain.usecases.workspace.update_workspace import UpdateWorkspace
from app.main.main import app
from app.presentation.factories.workspace_factories import (
    create_workspace_factory,
    delete_workspace_factory,
    get_workspace_factory,
    list_workspaces_factory,
    update_workspace_factory,
)


def _make_workspace() -> Workspace:
    return Workspace(name="Acme", slug="acme")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_list_workspaces(client: TestClient) -> None:
    w = _make_workspace()
    mock_uc = AsyncMock(spec=ListWorkspaces)
    mock_uc.execute.return_value = [w]
    app.dependency_overrides[list_workspaces_factory] = lambda: mock_uc
    try:
        response = client.get("/workspaces")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "acme"
    finally:
        app.dependency_overrides.clear()


def test_should_create_workspace(client: TestClient) -> None:
    w = _make_workspace()
    mock_uc = AsyncMock(spec=CreateWorkspace)
    mock_uc.execute.return_value = w
    app.dependency_overrides[create_workspace_factory] = lambda: mock_uc
    try:
        response = client.post("/workspaces", json={"name": "Acme", "slug": "acme"})
        assert response.status_code == 201
        assert response.json()["slug"] == "acme"
    finally:
        app.dependency_overrides.clear()


def test_should_get_workspace(client: TestClient) -> None:
    w = _make_workspace()
    mock_uc = AsyncMock(spec=GetWorkspace)
    mock_uc.execute.return_value = w
    app.dependency_overrides[get_workspace_factory] = lambda: mock_uc
    try:
        response = client.get(f"/workspaces/{w.id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Acme"
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_when_workspace_not_found(client: TestClient) -> None:
    mock_uc = AsyncMock(spec=GetWorkspace)
    wid = uuid.uuid4()
    mock_uc.execute.side_effect = NotFoundError(f"Workspace {wid} not found")
    app.dependency_overrides[get_workspace_factory] = lambda: mock_uc
    try:
        response = client.get(f"/workspaces/{wid}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_should_update_workspace(client: TestClient) -> None:
    w = _make_workspace()
    mock_uc = AsyncMock(spec=UpdateWorkspace)
    mock_uc.execute.return_value = w
    app.dependency_overrides[update_workspace_factory] = lambda: mock_uc
    try:
        response = client.put(f"/workspaces/{w.id}", json={"name": "Acme", "slug": "acme"})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_delete_workspace(client: TestClient) -> None:
    mock_uc = AsyncMock(spec=DeleteWorkspace)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_workspace_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/workspaces/{uuid.uuid4()}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("method", "path", "factory", "use_case"),
    [
        ("POST", "/workspaces", create_workspace_factory, CreateWorkspace),
        ("PUT", f"/workspaces/{uuid.uuid4()}", update_workspace_factory, UpdateWorkspace),
    ],
    ids=["create", "update"],
)
def test_should_return_409_when_the_slug_is_taken(
    client: TestClient,
    method: str,
    path: str,
    factory: Callable[..., object],
    use_case: type[object],
) -> None:
    mock_uc = AsyncMock(spec=use_case)
    mock_uc.execute.side_effect = ConflictError("Another workspace already uses this slug")
    app.dependency_overrides[factory] = lambda: mock_uc
    try:
        response = client.request(method, path, json={"name": "Acme", "slug": "acme"})
        assert response.status_code == 409
        assert response.json() == {"detail": "Another workspace already uses this slug"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("path", "method"), [("/workspaces", "post"), ("/workspaces/{workspace_id}", "put")]
)
def test_should_document_the_taken_slug_conflict(path: str, method: str) -> None:
    schema = app.openapi()
    conflict = schema["paths"][path][method]["responses"]["409"]
    assert conflict["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
    assert schema["components"]["schemas"]["ErrorResponse"]["required"] == ["detail"]
