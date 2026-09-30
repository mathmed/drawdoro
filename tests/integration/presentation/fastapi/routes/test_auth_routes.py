from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.common.settings import Environment, Settings, get_settings
from app.domain.entities.models.user import User
from app.domain.entities.models.workspace import Workspace
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.health.check_readiness import CheckReadiness
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces
from app.main.main import app
from app.presentation.factories.auth_factories import authenticate_user_factory
from app.presentation.factories.health_factories import check_readiness_factory
from app.presentation.factories.workspace_factories import list_workspaces_factory
from app.presentation.fastapi.configs.configs import make_fastapi_app

USER = User(email="ana@example.com", name="Ana Souza")


@pytest.fixture
def authenticate() -> AsyncMock:
    return AsyncMock(spec=AuthenticateUser)


@pytest.fixture
def client(authenticate: AsyncMock) -> Iterator[TestClient]:
    workspaces = AsyncMock(spec=ListWorkspaces)
    workspaces.execute.return_value = [Workspace(name="W", slug="w")]
    app.dependency_overrides[get_settings] = lambda: Settings(
        auth_enabled=True, service_api_key="svc-key"
    )
    app.dependency_overrides[authenticate_user_factory] = lambda: authenticate
    app.dependency_overrides[list_workspaces_factory] = lambda: workspaces
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_should_reject_requests_without_token(client: TestClient, authenticate: AsyncMock) -> None:
    authenticate.execute.side_effect = UnauthorizedError("Missing access token")
    assert client.get("/workspaces").status_code == 401


def test_should_allow_requests_with_valid_token(
    client: TestClient, authenticate: AsyncMock
) -> None:
    authenticate.execute.return_value = USER
    response = client.get("/workspaces", headers={"Authorization": "Bearer good"})
    assert response.status_code == 200
    assert authenticate.execute.await_args.args[0].token == "good"


def test_should_allow_trusted_service_with_api_key(
    client: TestClient, authenticate: AsyncMock
) -> None:
    assert client.get("/workspaces", headers={"X-API-Key": "svc-key"}).status_code == 200
    authenticate.execute.assert_not_awaited()


def test_should_reject_wrong_api_key(client: TestClient, authenticate: AsyncMock) -> None:
    authenticate.execute.side_effect = UnauthorizedError("Missing access token")
    assert client.get("/workspaces", headers={"X-API-Key": "nope"}).status_code == 401


def test_should_keep_health_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_should_keep_readiness_public(client: TestClient, authenticate: AsyncMock) -> None:
    app.dependency_overrides[check_readiness_factory] = lambda: AsyncMock(spec=CheckReadiness)
    assert client.get("/ready").status_code == 200
    authenticate.execute.assert_not_awaited()


def test_should_return_signed_in_user(client: TestClient, authenticate: AsyncMock) -> None:
    authenticate.execute.return_value = USER
    response = client.get("/me", headers={"Authorization": "Bearer good"})
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_should_return_signed_in_user_photo(client: TestClient, authenticate: AsyncMock) -> None:
    photo = "https://lh3.googleusercontent.com/a/ana"
    authenticate.execute.return_value = USER.model_copy(update={"picture_url": photo})
    response = client.get("/me", headers={"Authorization": "Bearer good"})
    assert response.json()["picture_url"] == photo


def test_should_close_websocket_without_valid_token(
    client: TestClient, authenticate: AsyncMock
) -> None:
    authenticate.execute.side_effect = UnauthorizedError("Missing access token")
    with (
        pytest.raises(WebSocketDisconnect) as closed,
        client.websocket_connect("/ws/diagrams/abc") as ws,
    ):
        ws.receive_text()
    assert closed.value.code == 1008


def test_should_return_404_for_me_when_auth_disabled() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=False)
    try:
        assert TestClient(app).get("/me").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_should_refuse_to_start_in_production_without_auth() -> None:
    with pytest.raises(RuntimeError, match="AUTH_ENABLED"):
        make_fastapi_app(Settings(env=Environment.PRODUCTION, auth_enabled=False))


def test_should_share_presence_and_free_the_seat_on_disconnect() -> None:
    from app.infra.realtime.connection_manager import manager

    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=False)
    try:
        with TestClient(app) as client, client.websocket_connect("/ws/diagrams/room-x") as ws:
            presence = ws.receive_json()
            assert presence["type"] == "presence"
            assert presence["users"][0]["name"] == "Guest"
            assert presence["you"] == presence["users"][0]["id"]
            ws.send_text("not json")
        assert manager.peer_count("room-x") == 0
    finally:
        app.dependency_overrides.clear()
