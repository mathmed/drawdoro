import uuid
from collections.abc import Callable, Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.api_key_owner import ApiKeyOwner
from app.domain.entities.models.created_api_key import CreatedApiKey
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.api_key.create_api_key import CreateApiKey
from app.domain.usecases.api_key.list_api_keys import ListApiKeys
from app.domain.usecases.api_key.revoke_api_key import RevokeApiKey
from app.domain.usecases.auth.authenticate_api_key import AuthenticateApiKey
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.main.main import app
from app.presentation.factories.api_key_factories import (
    create_api_key_factory,
    list_api_keys_factory,
    revoke_api_key_factory,
)
from app.presentation.factories.auth_factories import (
    authenticate_api_key_factory,
    authenticate_user_factory,
)

ANA = User(email="ana@example.com", name="Ana")
KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_abcdefg", key_hash="hash")
SESSION = {"Authorization": "Bearer good"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    authenticate = AsyncMock(spec=AuthenticateUser)
    authenticate.execute.return_value = ANA
    authenticate_key = AsyncMock(spec=AuthenticateApiKey)
    authenticate_key.execute.return_value = ApiKeyOwner(api_key=KEY, user=ANA)
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=True)
    app.dependency_overrides[authenticate_user_factory] = lambda: authenticate
    app.dependency_overrides[authenticate_api_key_factory] = lambda: authenticate_key
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def override(factory: Callable[..., object], spec: type, result: object = None) -> AsyncMock:
    mock = AsyncMock(spec=spec)
    mock.execute.return_value = result
    app.dependency_overrides[factory] = lambda: mock
    return mock


def test_should_create_a_key_and_show_its_secret_once(client: TestClient) -> None:
    mock = override(
        create_api_key_factory, CreateApiKey, CreatedApiKey(api_key=KEY, secret="mcpk_secret")
    )
    response = client.post("/me/api-keys", json={"label": "laptop"}, headers=SESSION)
    assert response.status_code == 201
    body = response.json()
    assert (body["secret"], body["label"], body["prefix"]) == ("mcpk_secret", "laptop", KEY.prefix)
    assert "key_hash" not in body
    params = mock.execute.await_args.args[0]
    assert (params.user_id, params.label) == (ANA.id, "laptop")


def test_should_reject_a_blank_label(client: TestClient) -> None:
    override(create_api_key_factory, CreateApiKey)
    assert client.post("/me/api-keys", json={"label": ""}, headers=SESSION).status_code == 422


def test_should_list_keys_without_secrets(client: TestClient) -> None:
    override(list_api_keys_factory, ListApiKeys, [KEY])
    response = client.get("/me/api-keys", headers=SESSION)
    assert response.status_code == 200
    [body] = response.json()
    assert "secret" not in body
    assert "key_hash" not in body
    assert body["last_used_at"] is None


def test_should_revoke_a_key(client: TestClient) -> None:
    mock = override(revoke_api_key_factory, RevokeApiKey)
    response = client.delete(f"/me/api-keys/{KEY.id}", headers=SESSION)
    assert response.status_code == 204
    assert mock.execute.await_args.args[0].key_id == KEY.id


def test_should_report_missing_keys(client: TestClient) -> None:
    mock = override(revoke_api_key_factory, RevokeApiKey)
    mock.execute.side_effect = NotFoundError("API key not found")
    assert client.delete(f"/me/api-keys/{uuid.uuid4()}", headers=SESSION).status_code == 404


def test_should_not_let_an_api_key_manage_keys(client: TestClient) -> None:
    create = override(create_api_key_factory, CreateApiKey)
    response = client.post(
        "/me/api-keys", json={"label": "more"}, headers={"X-API-Key": "mcpk_secret"}
    )
    assert response.status_code == 403
    create.execute.assert_not_awaited()
