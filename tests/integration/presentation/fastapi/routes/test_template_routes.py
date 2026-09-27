import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.template import Template
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.template.create_template import CreateTemplate
from app.domain.usecases.template.delete_template import DeleteTemplate
from app.domain.usecases.template.get_template import GetTemplate
from app.main.main import app
from app.presentation.factories.template_factories import (
    create_template_factory,
    delete_template_factory,
    get_template_factory,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_create_template(client: TestClient) -> None:
    template = Template(name="Base Template")
    mock_uc = AsyncMock(spec=CreateTemplate)
    mock_uc.execute.return_value = template
    app.dependency_overrides[create_template_factory] = lambda: mock_uc
    try:
        response = client.post("/templates", json={"name": "Base Template"})
        assert response.status_code == 201
        assert response.json()["name"] == "Base Template"
    finally:
        app.dependency_overrides.clear()


def test_should_get_template(client: TestClient) -> None:
    template = Template(name="Base Template")
    mock_uc = AsyncMock(spec=GetTemplate)
    mock_uc.execute.return_value = template
    app.dependency_overrides[get_template_factory] = lambda: mock_uc
    try:
        response = client.get(f"/templates/{template.id}")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_when_template_not_found(client: TestClient) -> None:
    tid = uuid.uuid4()
    mock_uc = AsyncMock(spec=GetTemplate)
    mock_uc.execute.side_effect = NotFoundError(f"Template {tid} not found")
    app.dependency_overrides[get_template_factory] = lambda: mock_uc
    try:
        response = client.get(f"/templates/{tid}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_should_delete_template(client: TestClient) -> None:
    tid = uuid.uuid4()
    mock_uc = AsyncMock(spec=DeleteTemplate)
    mock_uc.execute.return_value = None
    app.dependency_overrides[delete_template_factory] = lambda: mock_uc
    try:
        response = client.delete(f"/templates/{tid}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
