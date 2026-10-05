import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.common.settings import Settings, get_settings
from app.domain.constants.presence import WORKSPACE_PRESENCE_MESSAGE_BURST
from app.domain.contracts.workspace_presence import WorkspacePresence
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.user import User
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import NotFoundError, UnauthorizedError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.get_diagram_location import GetDiagramLocation
from app.infra.realtime.workspace_presence_hub import workspace_presence_hub
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.diagram_factories import (
    get_diagram_by_share_token_factory,
    get_diagram_location_factory,
)
from app.presentation.factories.presence_factories import (
    PresenceAccess,
    PresenceAccessScope,
    presence_access_factory,
    workspace_presence_factory,
)
from app.presentation.fastapi.routes import workspace_presence_routes
from tests.doubles import double

ANA = User(email="ana@example.com", name="Ana", picture_url="https://example.com/ana.png")
POLICY_VIOLATION = 1008


class Workspace:
    def __init__(self) -> None:
        self.id = uuid.uuid4()
        self.project_id = uuid.uuid4()
        self.diagram_id = uuid.uuid4()

    @property
    def location(self) -> DiagramLocation:
        return DiagramLocation(workspace_id=self.id, project_id=self.project_id)

    def presence_url(self, query: str = "?token=id-token") -> str:
        return f"/ws/workspaces/{self.id}/presence{query}"

    def diagram_url(self, query: str = "?token=id-token") -> str:
        return f"/ws/diagrams/{self.diagram_id}{query}"


@pytest.fixture
def authenticate() -> AsyncMock:
    mock = AsyncMock(spec=AuthenticateUser)
    mock.execute.return_value = ANA
    return mock


@pytest.fixture
def authorize() -> AsyncMock:
    return AsyncMock(spec=AuthorizeWorkspaceAccess)


@pytest.fixture
def workspace() -> Workspace:
    return Workspace()


@pytest.fixture
def other_workspace() -> Workspace:
    return Workspace()


@pytest.fixture
def shared_lookup(workspace: Workspace) -> AsyncMock:
    mock = AsyncMock(spec=GetDiagramByShareToken)
    mock.execute.return_value = Diagram(
        id=workspace.diagram_id, project_id=workspace.project_id, name="Checkout"
    )
    return mock


@pytest.fixture
def locate(workspace: Workspace, other_workspace: Workspace) -> AsyncMock:
    places = {
        workspace.diagram_id: workspace.location,
        other_workspace.diagram_id: other_workspace.location,
    }
    mock = AsyncMock(spec=GetDiagramLocation)
    mock.execute.side_effect = lambda params: places[params.diagram_id]
    return mock


@pytest.fixture(autouse=True)
def fast_batches(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(workspace_presence_hub, "_batch_seconds", 0.01)


def scope_of(authenticate: AsyncMock, authorize: AsyncMock) -> PresenceAccessScope:
    @asynccontextmanager
    async def scope() -> AsyncIterator[PresenceAccess]:
        yield PresenceAccess(authenticate=authenticate, authorize=authorize)

    return scope


def serve(auth_enabled: bool, overrides: dict[Any, object]) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=auth_enabled)
    for factory, value in overrides.items():
        app.dependency_overrides[factory] = lambda value=value: value
    # One event loop for every connection, as in the server: the rooms reach the sidebars.
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client(
    authenticate: AsyncMock, authorize: AsyncMock, shared_lookup: AsyncMock, locate: AsyncMock
) -> Iterator[TestClient]:
    yield from serve(
        True,
        {
            presence_access_factory: scope_of(authenticate, authorize),
            authenticate_user_factory: authenticate,
            authorize_workspace_access_factory: authorize,
            get_diagram_by_share_token_factory: shared_lookup,
            get_diagram_location_factory: locate,
        },
    )


@pytest.fixture
def open_client(locate: AsyncMock) -> Iterator[TestClient]:
    yield from serve(False, {get_diagram_location_factory: locate})


def closed_code(client: TestClient, url: str) -> int:
    with pytest.raises(WebSocketDisconnect) as closed, client.websocket_connect(url) as ws:
        ws.receive_text()
    return closed.value.code


ANA_JSON = {"id": str(ANA.id), "name": "Ana", "kind": "person", "picture_url": ANA.picture_url}


def test_should_show_a_member_who_joins_and_leaves_a_diagram(
    client: TestClient, workspace: Workspace, authorize: AsyncMock
) -> None:
    with client.websocket_connect(workspace.presence_url()) as sidebar:
        assert sidebar.receive_json() == {
            "type": "presence_snapshot",
            "you": str(ANA.id),
            "diagrams": [],
        }
        params = authorize.execute.await_args.args[0]
        assert (params.user_id, params.required_role, params.workspace_id) == (
            ANA.id,
            WorkspaceRole.VIEWER,
            workspace.id,
        )

        with client.websocket_connect(workspace.diagram_url()) as editor:
            editor.receive_json()
            assert sidebar.receive_json() == {
                "type": "presence_delta",
                "diagrams": [
                    {
                        "diagram_id": str(workspace.diagram_id),
                        "project_id": str(workspace.project_id),
                        "users": [ANA_JSON],
                    }
                ],
            }

        assert sidebar.receive_json()["diagrams"][0]["users"] == []


def test_should_snapshot_who_is_already_in_the_workspace(
    client: TestClient, workspace: Workspace
) -> None:
    with client.websocket_connect(workspace.diagram_url()) as editor:
        editor.receive_json()
        with client.websocket_connect(workspace.presence_url()) as sidebar:
            snapshot = sidebar.receive_json()

    assert snapshot["diagrams"] == [
        {
            "diagram_id": str(workspace.diagram_id),
            "project_id": str(workspace.project_id),
            "users": [ANA_JSON],
        }
    ]


def test_should_show_a_guest_on_a_share_link_to_the_members(
    client: TestClient, workspace: Workspace
) -> None:
    with client.websocket_connect(workspace.presence_url()) as sidebar:
        sidebar.receive_json()
        with client.websocket_connect(workspace.diagram_url("?share=tok&name=Carla")) as guest:
            guest.receive_json()
            users = sidebar.receive_json()["diagrams"][0]["users"]

    assert [(user["name"], user["kind"]) for user in users] == [("Carla", "person")]


def test_should_keep_other_workspaces_presence_out(
    client: TestClient, workspace: Workspace, other_workspace: Workspace
) -> None:
    with client.websocket_connect(workspace.presence_url()) as sidebar:
        sidebar.receive_json()
        with client.websocket_connect(other_workspace.diagram_url()) as elsewhere:
            elsewhere.receive_json()
            with client.websocket_connect(workspace.diagram_url()) as here:
                here.receive_json()
                # Had the other workspace's diagram leaked, it would arrive first.
                delta = sidebar.receive_json()

    assert [item["diagram_id"] for item in delta["diagrams"]] == [str(workspace.diagram_id)]


@pytest.mark.parametrize(
    "query",
    ["", "?token=", "?share=tok&name=Carla"],
    ids=["no token", "empty token", "share link guest"],
)
def test_should_refuse_visitors_without_a_session(
    client: TestClient, workspace: Workspace, authenticate: AsyncMock, query: str
) -> None:
    assert closed_code(client, workspace.presence_url(query)) == POLICY_VIOLATION
    authenticate.execute.assert_not_awaited()


def test_should_refuse_a_rejected_token(
    client: TestClient, workspace: Workspace, authenticate: AsyncMock, authorize: AsyncMock
) -> None:
    authenticate.execute.side_effect = UnauthorizedError("Invalid or expired token")
    assert closed_code(client, workspace.presence_url()) == POLICY_VIOLATION
    authorize.execute.assert_not_awaited()


def test_should_refuse_someone_outside_the_workspace(
    client: TestClient, workspace: Workspace, authorize: AsyncMock
) -> None:
    authorize.execute.side_effect = NotFoundError("Workspace not found")
    assert closed_code(client, workspace.presence_url()) == POLICY_VIOLATION


def test_should_refuse_a_workspace_id_that_is_not_a_uuid(
    client: TestClient, authenticate: AsyncMock
) -> None:
    assert closed_code(client, "/ws/workspaces/condoconta/presence?token=t") == POLICY_VIOLATION
    authenticate.execute.assert_not_awaited()


def test_should_cut_off_a_member_removed_from_the_workspace(
    client: TestClient, workspace: Workspace, authorize: AsyncMock, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(workspace_presence_routes, "WORKSPACE_PRESENCE_RECHECK_SECONDS", 0.05)
    authorize.execute.side_effect = [None, None, NotFoundError("Workspace not found")]
    with client.websocket_connect(workspace.presence_url()) as sidebar:
        sidebar.receive_json()
        with pytest.raises(WebSocketDisconnect) as closed:
            sidebar.receive_json()

    assert closed.value.code == POLICY_VIOLATION
    assert authorize.execute.await_count == 3


def test_should_cut_off_a_client_that_floods_the_channel(
    client: TestClient, workspace: Workspace, monkeypatch: MonkeyPatch
) -> None:
    # A frozen clock never refills the budget, so the message after the burst ends it.
    monkeypatch.setattr(workspace_presence_routes, "monotonic", lambda: 0.0)
    with client.websocket_connect(workspace.presence_url()) as sidebar:
        sidebar.receive_json()
        for _ in range(WORKSPACE_PRESENCE_MESSAGE_BURST):
            sidebar.send_text("hello")
        sidebar.send_bytes(b"\x00")
        with pytest.raises(WebSocketDisconnect) as closed:
            sidebar.receive_json()

    assert closed.value.code == POLICY_VIOLATION


def test_should_refuse_more_sidebars_than_allowed_and_free_them_on_close(
    client: TestClient, workspace: Workspace, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(workspace_presence_hub, "_subscriptions_per_viewer", 1)
    with client.websocket_connect(workspace.presence_url()) as first:
        first.receive_json()
        assert closed_code(client, workspace.presence_url()) == POLICY_VIOLATION

    with client.websocket_connect(workspace.presence_url()) as again:
        assert again.receive_json()["type"] == "presence_snapshot"


def test_should_share_presence_when_authentication_is_disabled(
    open_client: TestClient, workspace: Workspace
) -> None:
    with open_client.websocket_connect(workspace.presence_url("")) as sidebar:
        assert sidebar.receive_json()["you"] is None
        with open_client.websocket_connect(workspace.diagram_url("")) as editor:
            editor.receive_json()
            users = sidebar.receive_json()["diagrams"][0]["users"]

    assert [user["name"] for user in users] == ["Guest"]


def test_should_free_the_subscription_when_the_client_drops_while_joining(
    open_client: TestClient, workspace: Workspace
) -> None:
    async def accept_then_drop(ws: WebSocket, *_: object) -> bool:
        await ws.accept()
        raise WebSocketDisconnect(code=1006)

    presence = double(WorkspacePresence)
    presence.subscribe.side_effect = accept_then_drop
    app.dependency_overrides[workspace_presence_factory] = lambda: presence

    with open_client.websocket_connect(workspace.presence_url("")):
        pass

    presence.unsubscribe.assert_called_once()
    assert presence.unsubscribe.call_args.args[1] == workspace.id


def test_should_end_the_subscription_when_membership_cannot_be_checked(
    client: TestClient, workspace: Workspace, authorize: AsyncMock, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(workspace_presence_routes, "WORKSPACE_PRESENCE_RECHECK_SECONDS", 0.05)
    authorize.execute.side_effect = [None, OSError("database unreachable")]
    with (
        pytest.raises(OSError, match="database unreachable"),
        client.websocket_connect(workspace.presence_url()) as sidebar,
    ):
        sidebar.receive_json()
        sidebar.receive_json()
