import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.comment import Comment
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.documentation_page import DocumentationPage
from app.domain.usecases.comment.create_comment import CreateComment
from app.domain.usecases.comment.delete_comment import DeleteComment
from app.domain.usecases.diagram.create_diagram import CreateDiagram
from app.domain.usecases.diagram.delete_diagram import DeleteDiagram
from app.domain.usecases.diagram.get_diagram import GetDiagram
from app.domain.usecases.diagram.update_diagram import UpdateDiagram
from app.domain.usecases.documentation.upsert_documentation_page import UpsertDocumentationPage
from app.main.main import app
from app.presentation.factories.comment_factories import (
    create_comment_factory,
    delete_comment_factory,
)
from app.presentation.factories.diagram_factories import (
    create_diagram_factory,
    delete_diagram_factory,
    get_diagram_factory,
    update_diagram_factory,
)
from app.presentation.factories.documentation_factories import upsert_documentation_page_factory


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_create_diagram(client: TestClient) -> None:
    project_id = uuid.uuid4()
    diagram = Diagram(project_id=project_id, name="My Diagram")
    mock_uc = AsyncMock(spec=CreateDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[create_diagram_factory] = lambda: mock_uc
    try:
        response = client.post(f"/projects/{project_id}/diagrams", json={"name": "My Diagram"})
        assert response.status_code == 201
        assert response.json()["name"] == "My Diagram"
    finally:
        app.dependency_overrides.clear()


def test_should_get_diagram(client: TestClient) -> None:
    project_id = uuid.uuid4()
    diagram = Diagram(project_id=project_id, name="My Diagram")
    mock_uc = AsyncMock(spec=GetDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[get_diagram_factory] = lambda: mock_uc
    try:
        response = client.get(f"/projects/{project_id}/diagrams/{diagram.id}")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_update_diagram(client: TestClient) -> None:
    project_id = uuid.uuid4()
    diagram = Diagram(project_id=project_id, name="Updated")
    mock_uc = AsyncMock(spec=UpdateDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[update_diagram_factory] = lambda: mock_uc
    try:
        response = client.put(
            f"/projects/{project_id}/diagrams/{diagram.id}", json={"name": "Updated"}
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_delete_diagram(client: TestClient) -> None:
    project_id = uuid.uuid4()
    did = uuid.uuid4()
    mock_uc = AsyncMock(spec=DeleteDiagram)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_diagram_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/projects/{project_id}/diagrams/{did}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_should_upsert_documentation(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    page = DocumentationPage(diagram_id=diagram_id, content="Hello")
    mock_uc = AsyncMock(spec=UpsertDocumentationPage)
    mock_uc.execute.return_value = page
    app.dependency_overrides[upsert_documentation_page_factory] = lambda: mock_uc
    try:
        response = client.put(f"/diagrams/{diagram_id}/documentation", json={"content": "Hello"})
        assert response.status_code == 200
        assert response.json()["content"] == "Hello"
    finally:
        app.dependency_overrides.clear()


def test_should_create_comment(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    comment = Comment(diagram_id=diagram_id, element_id="el1", content="Nice!")
    mock_uc = AsyncMock(spec=CreateComment)
    mock_uc.execute.return_value = comment
    app.dependency_overrides[create_comment_factory] = lambda: mock_uc
    try:
        response = client.post(
            f"/diagrams/{diagram_id}/comments",
            json={"element_id": "el1", "content": "Nice!"},
        )
        assert response.status_code == 201
        assert response.json()["content"] == "Nice!"
    finally:
        app.dependency_overrides.clear()


def test_should_return_comment_author_name(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    comment = Comment(
        diagram_id=diagram_id,
        element_id="el1",
        content="Nice!",
        author_id=uuid.uuid4(),
        author_name="Ana Souza",
    )
    mock_uc = AsyncMock(spec=CreateComment)
    mock_uc.execute.return_value = comment
    app.dependency_overrides[create_comment_factory] = lambda: mock_uc
    try:
        response = client.post(
            f"/diagrams/{diagram_id}/comments", json={"element_id": "el1", "content": "Nice!"}
        )
        assert response.json()["author_name"] == "Ana Souza"
    finally:
        app.dependency_overrides.clear()


def test_should_delete_comment(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    comment_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=DeleteComment)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_comment_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/diagrams/{diagram_id}/comments/{comment_id}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_should_get_diagram_by_id_alone(client: TestClient) -> None:
    diagram = Diagram(project_id=uuid.uuid4(), name="From a link")
    mock_uc = AsyncMock(spec=GetDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[get_diagram_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram.id}")
        assert response.status_code == 200
        assert response.json()["project_id"] == str(diagram.project_id)
        assert mock_uc.execute.await_args.args[0].diagram_id == diagram.id
    finally:
        app.dependency_overrides.clear()
