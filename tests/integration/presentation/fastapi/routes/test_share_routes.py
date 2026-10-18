import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.share_diagram import ShareDiagram
from app.infra.database.models.diagram import DiagramORM
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
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


def test_should_pass_the_share_token_to_the_use_case_as_it_is(client: TestClient) -> None:
    mock_uc = AsyncMock(spec=GetDiagramByShareToken)
    mock_uc.execute.side_effect = NotFoundError("Shared diagram not found")
    app.dependency_overrides[get_diagram_by_share_token_factory] = lambda: mock_uc
    try:
        response = client.get("/share/tok%00en")
        assert response.status_code == 404
        assert mock_uc.execute.await_args.args[0].share_token == "tok\x00en"
    finally:
        app.dependency_overrides.clear()


# A database that would find the diagram of "token": a NUL anywhere in the link must not open it.
@pytest.mark.parametrize(
    ("path", "status_code"),
    [("token", 200), ("tok%00en", 404), ("%00token", 404), ("token%00", 404)],
)
def test_should_never_open_a_diagram_through_a_token_with_nul_characters(
    client: TestClient, path: str, status_code: int
) -> None:
    now = datetime.now(UTC)
    stored = DiagramORM(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        folder_id=None,
        name="Shared",
        canvas_state=None,
        semantic_metadata=None,
        share_token="token",
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = stored
    session.execute.return_value = result
    app.dependency_overrides[get_diagram_by_share_token_factory] = lambda: GetDiagramByShareToken(
        DiagramRepositoryImpl(session)
    )
    try:
        response = client.get(f"/share/{path}")
        assert response.status_code == status_code
        if status_code == 404:
            assert response.json() == {"detail": "Shared diagram not found"}
            session.execute.assert_not_awaited()
    finally:
        app.dependency_overrides.clear()
