import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.adr import Adr
from app.domain.enums.adr_status import AdrStatus
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.adr.create_adr import CreateAdr
from app.domain.usecases.adr.delete_adr import DeleteAdr
from app.domain.usecases.adr.get_adr import GetAdr
from app.domain.usecases.adr.list_adrs import ListAdrs
from app.domain.usecases.adr.update_adr import UpdateAdr
from app.main.main import app
from app.presentation.factories.adr_factories import (
    create_adr_factory,
    delete_adr_factory,
    get_adr_factory,
    list_adrs_factory,
    update_adr_factory,
)


def _make_adr(diagram_id: uuid.UUID) -> Adr:
    return Adr(
        diagram_id=diagram_id,
        title="Use PostgreSQL",
        context="We need a database",
        decision="Use PostgreSQL",
        consequences="Need to manage DB",
        status=AdrStatus.PROPOSED,
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_list_adrs(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    mock_uc = AsyncMock(spec=ListAdrs)
    mock_uc.execute.return_value = [adr]
    app.dependency_overrides[list_adrs_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram_id}/adrs")
        assert response.status_code == 200
        assert len(response.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_should_create_adr(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    mock_uc = AsyncMock(spec=CreateAdr)
    mock_uc.execute.return_value = adr
    app.dependency_overrides[create_adr_factory] = lambda: mock_uc
    try:
        response = client.post(
            f"/diagrams/{diagram_id}/adrs",
            json={
                "title": "Use PostgreSQL",
                "context": "We need a database",
                "decision": "Use PostgreSQL",
                "consequences": "Need to manage DB",
                "status": "proposed",
            },
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Use PostgreSQL"
    finally:
        app.dependency_overrides.clear()


def test_should_get_adr(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    mock_uc = AsyncMock(spec=GetAdr)
    mock_uc.execute.return_value = adr
    app.dependency_overrides[get_adr_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram_id}/adrs/{adr.id}")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_when_adr_not_found(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    adr_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=GetAdr)
    mock_uc.execute.side_effect = NotFoundError(f"ADR {adr_id} not found")
    app.dependency_overrides[get_adr_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram_id}/adrs/{adr_id}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_should_update_adr(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    mock_uc = AsyncMock(spec=UpdateAdr)
    mock_uc.execute.return_value = adr
    app.dependency_overrides[update_adr_factory] = lambda: mock_uc
    try:
        response = client.put(
            f"/diagrams/{diagram_id}/adrs/{adr.id}",
            json={
                "title": "Use PostgreSQL",
                "context": "We need a database",
                "decision": "Use PostgreSQL",
                "consequences": "Need to manage DB",
                "status": "accepted",
            },
        )
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_delete_adr(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    adr_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=DeleteAdr)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_adr_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/diagrams/{diagram_id}/adrs/{adr_id}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
