import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.share_diagram import ShareDiagram
from app.main.main import app
from app.presentation.factories.diagram_factories import (
    get_diagram_by_share_token_factory,
    share_diagram_factory,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_generate_share_token(client: TestClient) -> None:
    diagram = Diagram(project_id=uuid.uuid4(), name="Diagram", share_token="abc123")
    mock_uc = AsyncMock(spec=ShareDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[share_diagram_factory] = lambda: mock_uc
    try:
        response = client.post(f"/diagrams/{diagram.id}/share")
        assert response.status_code == 201
        assert response.json() == {"share_token": "abc123"}
    finally:
        app.dependency_overrides.clear()


def test_should_return_shared_diagram(client: TestClient) -> None:
    diagram = Diagram(project_id=uuid.uuid4(), name="Shared", canvas_state={"a": 1})
    mock_uc = AsyncMock(spec=GetDiagramByShareToken)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[get_diagram_by_share_token_factory] = lambda: mock_uc
    try:
        response = client.get("/share/abc123")
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Shared"
        assert body["canvas_state"] == {"a": 1}
        assert "project_id" not in body
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_for_unknown_share_token(client: TestClient) -> None:
    mock_uc = AsyncMock(spec=GetDiagramByShareToken)
    mock_uc.execute.side_effect = NotFoundError("Shared diagram not found")
    app.dependency_overrides[get_diagram_by_share_token_factory] = lambda: mock_uc
    try:
        response = client.get("/share/missing")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
