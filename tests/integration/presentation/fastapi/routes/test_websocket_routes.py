import uuid
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from starlette.websockets import WebSocketDisconnect

from app.common.settings import Settings, get_settings
from app.domain.constants.presence import CURSOR_MESSAGE_BURST
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.user import User
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import NotFoundError, UnauthorizedError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.get_diagram_location import GetDiagramLocation
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.diagram_factories import (
    get_diagram_by_share_token_factory,
    get_diagram_location_factory,
)
from app.presentation.fastapi.routes import websocket_routes

ANA = User(email="ana@example.com", name="Ana", picture_url="https://example.com/ana.png")
POLICY_VIOLATION = 1008


# The rooms here are not real diagrams: none of them is placed in a workspace.
@pytest.fixture(autouse=True)
def locate() -> Iterator[AsyncMock]:
    mock = AsyncMock(spec=GetDiagramLocation)
    mock.execute.side_effect = NotFoundError("Diagram not found")
    app.dependency_overrides[get_diagram_location_factory] = lambda: mock
    yield mock
    app.dependency_overrides.clear()


def test_should_send_presence_on_connect() -> None:
    client = TestClient(app)
    diagram_id = uuid.uuid4()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}") as ws:
        data = ws.receive_json()
        assert data["type"] == "presence"
        assert data["peers"] == 1


def test_should_keep_socket_open_after_update_without_peers() -> None:
    client = TestClient(app)
    diagram_id = uuid.uuid4()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}") as ws:
        assert ws.receive_json()["type"] == "presence"
        # With no other peers connected, updates are simply not echoed back and
        # the socket stays healthy.
        ws.send_json({"type": "update", "client_id": "solo", "snapshot": {}})
        ws.send_json({"type": "cursor", "point": {"x": 1, "y": 2}, "page": "page:page"})


@pytest.fixture
def authenticate() -> AsyncMock:
    mock = AsyncMock(spec=AuthenticateUser)
    mock.execute.return_value = ANA
    return mock


@pytest.fixture
def authorize() -> AsyncMock:
    return AsyncMock(spec=AuthorizeWorkspaceAccess)


@pytest.fixture
def shared_lookup() -> AsyncMock:
    return AsyncMock(spec=GetDiagramByShareToken)


@pytest.fixture
def client(
    authenticate: AsyncMock, authorize: AsyncMock, shared_lookup: AsyncMock
) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=True)
    app.dependency_overrides[authenticate_user_factory] = lambda: authenticate
    app.dependency_overrides[authorize_workspace_access_factory] = lambda: authorize
    app.dependency_overrides[get_diagram_by_share_token_factory] = lambda: shared_lookup
    # One event loop for every connection, as in the server: sockets reach each other's rooms.
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def guest_client() -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=False)
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def room() -> str:
    return str(uuid.uuid4())


def closed_code(client: TestClient, url: str) -> int:
    with pytest.raises(WebSocketDisconnect) as closed, client.websocket_connect(url) as ws:
        ws.receive_text()
    return closed.value.code


def test_should_admit_a_signed_in_viewer_with_their_profile(
    client: TestClient, authenticate: AsyncMock, authorize: AsyncMock
) -> None:
    diagram_id = room()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}?token=id-token") as ws:
        presence = ws.receive_json()

    assert presence == {
        "type": "presence",
        "users": [
            {"id": str(ANA.id), "name": "Ana", "kind": "person", "picture_url": ANA.picture_url}
        ],
        "you": str(ANA.id),
        "peers": 1,
    }
    authenticate.execute.assert_awaited_once()
    assert authenticate.execute.await_args.args[0].token == "id-token"
    params = authorize.execute.await_args.args[0]
    assert (params.user_id, params.required_role, params.diagram_id) == (
        ANA.id,
        WorkspaceRole.VIEWER,
        uuid.UUID(diagram_id),
    )


def test_should_close_when_the_token_is_rejected(
    client: TestClient, authenticate: AsyncMock
) -> None:
    authenticate.execute.side_effect = UnauthorizedError("Invalid or expired token")
    assert closed_code(client, f"/ws/diagrams/{room()}?token=bad") == POLICY_VIOLATION


def test_should_close_when_the_user_cannot_read_the_diagram(
    client: TestClient, authorize: AsyncMock, locate: AsyncMock
) -> None:
    authorize.execute.side_effect = NotFoundError("Workspace not found")
    assert closed_code(client, f"/ws/diagrams/{room()}?token=id-token") == POLICY_VIOLATION
    locate.execute.assert_not_awaited()


def test_should_look_up_where_the_diagram_is_once_admitted(
    client: TestClient, locate: AsyncMock
) -> None:
    diagram_id = room()
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}?token=id-token") as ws:
        assert ws.receive_json()["type"] == "presence"
    assert locate.execute.await_args.args[0].diagram_id == uuid.UUID(diagram_id)


def test_should_close_when_the_diagram_id_is_not_a_uuid(client: TestClient) -> None:
    assert closed_code(client, "/ws/diagrams/not-a-uuid?token=id-token") == POLICY_VIOLATION


def test_should_admit_a_guest_with_a_share_link_under_their_name(
    client: TestClient, authenticate: AsyncMock, shared_lookup: AsyncMock
) -> None:
    diagram_id = room()
    shared_lookup.execute.return_value = Diagram(
        id=uuid.UUID(diagram_id), project_id=uuid.uuid4(), name="Checkout"
    )
    with client.websocket_connect(f"/ws/diagrams/{diagram_id}?share=tok&name=Carla") as ws:
        presence = ws.receive_json()

    assert [user["name"] for user in presence["users"]] == ["Carla"]
    assert presence["users"][0]["id"] == presence["you"]
    authenticate.execute.assert_not_awaited()
    assert shared_lookup.execute.await_args.args[0].share_token == "tok"


def receive_until(ws: Any, kind: str) -> dict[str, Any]:
    while True:
        message: dict[str, Any] = ws.receive_json()
        if message.get("type") == kind:
            return message


def test_should_relay_edits_to_the_other_editors_only(
    guest_client: TestClient,
) -> None:
    url = f"/ws/diagrams/{room()}"
    with (
        guest_client.websocket_connect(url) as first,
        guest_client.websocket_connect(url) as second,
    ):
        assert receive_until(first, "presence")["peers"] == 1
        assert receive_until(first, "presence")["peers"] == 2
        assert receive_until(second, "presence")["peers"] == 2

        first.send_json({"type": "update", "changes": [1]})
        assert second.receive_json() == {"type": "update", "changes": [1]}

        # Had the update been echoed to its sender, it would arrive before this one.
        second.send_json({"type": "update", "changes": [2]})
        assert first.receive_json() == {"type": "update", "changes": [2]}


def test_should_drop_messages_that_are_not_edits_or_cursors(guest_client: TestClient) -> None:
    url = f"/ws/diagrams/{room()}"
    with (
        guest_client.websocket_connect(url) as first,
        guest_client.websocket_connect(url) as second,
    ):
        receive_until(first, "presence")
        receive_until(first, "presence")
        receive_until(second, "presence")

        first.send_json({"type": "chat", "text": "hi"})
        first.send_text("not json")
        first.send_text("[1, 2]")
        first.send_json({"no": "type"})
        first.send_json({"type": "update", "changes": [2]})

        assert second.receive_json() == {"type": "update", "changes": [2]}


def test_should_tell_the_others_when_someone_leaves(guest_client: TestClient) -> None:
    url = f"/ws/diagrams/{room()}"
    with guest_client.websocket_connect(url) as staying:
        receive_until(staying, "presence")
        with guest_client.websocket_connect(url) as leaving:
            receive_until(leaving, "presence")
            assert receive_until(staying, "presence")["peers"] == 2
            # Closed from the client side while the session is still running, like a closed tab.
            leaving.close()
            presence = receive_until(staying, "presence")

    assert presence["peers"] == 1
    assert presence["users"][0]["id"] == presence["you"]


CURSOR = {"type": "cursor", "point": {"x": 12.5, "y": -3}, "page": "page:page"}


def test_should_relay_a_cursor_to_the_others_under_the_sender_identity(
    client: TestClient, authenticate: AsyncMock, shared_lookup: AsyncMock
) -> None:
    diagram_id = room()
    shared_lookup.execute.return_value = Diagram(
        id=uuid.UUID(diagram_id), project_id=uuid.uuid4(), name="Checkout"
    )
    url = f"/ws/diagrams/{diagram_id}"
    with (
        client.websocket_connect(f"{url}?token=id-token") as ana,
        client.websocket_connect(f"{url}?share=tok&name=Carla") as carla,
    ):
        receive_until(ana, "presence")
        carla_id = receive_until(carla, "presence")["you"]

        carla.send_json(CURSOR | {"id": "forged"})
        carla.send_json(CURSOR)
        ana.send_json({"type": "cursor", "point": None})

        assert receive_until(ana, "cursor") == {
            "type": "cursor",
            "id": carla_id,
            "name": "Carla",
            "point": {"x": 12.5, "y": -3.0},
            "page": "page:page",
        }
        assert receive_until(carla, "cursor") == {
            "type": "cursor",
            "id": str(ANA.id),
            "name": "Ana",
            "point": None,
            "page": None,
        }


def test_should_drop_malformed_cursors_without_closing_the_session(
    guest_client: TestClient,
) -> None:
    url = f"/ws/diagrams/{room()}"
    with (
        guest_client.websocket_connect(url) as first,
        guest_client.websocket_connect(url) as second,
    ):
        receive_until(first, "presence")
        receive_until(first, "presence")
        receive_until(second, "presence")

        first.send_json({"type": "cursor", "x": 4})
        first.send_json({"type": "cursor", "point": {"x": "far", "y": 1}, "page": "page:page"})
        first.send_json(CURSOR)

        assert second.receive_json()["point"] == {"x": 12.5, "y": -3.0}


def next_relayed(ws: Any) -> dict[str, Any]:
    while True:
        message: dict[str, Any] = ws.receive_json()
        if message.get("type") != "presence":
            return message


def test_should_keep_cursors_inside_their_diagram(guest_client: TestClient) -> None:
    here, elsewhere = f"/ws/diagrams/{room()}", f"/ws/diagrams/{room()}"
    with (
        guest_client.websocket_connect(here) as sender,
        guest_client.websocket_connect(here) as peer,
        guest_client.websocket_connect(elsewhere) as watcher,
        guest_client.websocket_connect(elsewhere) as neighbour,
    ):
        receive_until(sender, "presence")
        receive_until(peer, "presence")
        receive_until(watcher, "presence")
        receive_until(neighbour, "presence")

        sender.send_json(CURSOR)
        assert receive_until(peer, "cursor")["point"] == {"x": 12.5, "y": -3.0}
        neighbour.send_json({"type": "update", "changes": [1]})

        # Had the cursor leaked into the other diagram, it would arrive before the update.
        assert next_relayed(watcher) == {"type": "update", "changes": [1]}


def test_should_cut_a_cursor_flood_down_to_the_budget(
    guest_client: TestClient, monkeypatch: MonkeyPatch
) -> None:
    # A frozen clock never refills the budget, so exactly one burst gets through.
    monkeypatch.setattr(websocket_routes, "monotonic", lambda: 0.0)
    url = f"/ws/diagrams/{room()}"
    with (
        guest_client.websocket_connect(url) as flooder,
        guest_client.websocket_connect(url) as watcher,
    ):
        receive_until(flooder, "presence")
        receive_until(flooder, "presence")
        receive_until(watcher, "presence")

        for _ in range(CURSOR_MESSAGE_BURST + 5):
            flooder.send_json(CURSOR)
        flooder.send_json({"type": "update", "changes": [1]})

        received = []
        while (message := watcher.receive_json())["type"] == "cursor":
            received.append(message)

    assert len(received) == CURSOR_MESSAGE_BURST
    assert message == {"type": "update", "changes": [1]}
