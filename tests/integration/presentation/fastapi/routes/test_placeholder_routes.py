from fastapi.testclient import TestClient
from pytest import fixture

from app.main.main import app


@fixture
def client() -> TestClient:
    return TestClient(app)


def test_should_return_501_for_list_workspaces(client: TestClient) -> None:
    response = client.get("/workspaces")
    assert response.status_code == 501


def test_should_return_501_for_create_workspace(client: TestClient) -> None:
    response = client.post("/workspaces", json={})
    assert response.status_code == 501


def test_should_return_501_for_get_workspace(client: TestClient) -> None:
    response = client.get("/workspaces/abc")
    assert response.status_code == 501


def test_should_return_501_for_list_projects(client: TestClient) -> None:
    response = client.get("/workspaces/abc/projects")
    assert response.status_code == 501


def test_should_return_501_for_list_folders(client: TestClient) -> None:
    response = client.get("/projects/abc/folders")
    assert response.status_code == 501


def test_should_return_501_for_list_diagrams(client: TestClient) -> None:
    response = client.get("/projects/abc/diagrams")
    assert response.status_code == 501


def test_should_return_501_for_get_documentation(client: TestClient) -> None:
    response = client.get("/diagrams/abc/documentation")
    assert response.status_code == 501


def test_should_return_501_for_list_comments(client: TestClient) -> None:
    response = client.get("/diagrams/abc/comments")
    assert response.status_code == 501


def test_should_return_501_for_list_templates(client: TestClient) -> None:
    response = client.get("/templates")
    assert response.status_code == 501


def test_should_return_501_for_list_adrs(client: TestClient) -> None:
    response = client.get("/diagrams/abc/adrs")
    assert response.status_code == 501
