import json
import uuid
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from app.domain.entities.models.diagram import Diagram
from app.infra.realtime.connection_manager import ConnectionManager, Participant
from app.infra.realtime.realtime_diagram_update_notifier import RealtimeDiagramUpdateNotifier

DIAGRAM = Diagram(
    project_id=uuid.uuid4(),
    folder_id=uuid.uuid4(),
    name="Checkout",
    canvas_state={"shapes": ["box"]},
    semantic_metadata={"shape:1": {"type": "service"}},
    share_token="secret-share-token",
    updated_at=datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
)


def make_ws() -> WebSocket:
    return cast(WebSocket, AsyncMock(spec=WebSocket))


def sent(ws: WebSocket) -> list[dict[str, object]]:
    return [json.loads(call.args[0]) for call in cast(AsyncMock, ws.send_text).await_args_list]


@pytest.fixture
def connections() -> ConnectionManager:
    return ConnectionManager()


@pytest.fixture
def sut(connections: ConnectionManager) -> RealtimeDiagramUpdateNotifier:
    return RealtimeDiagramUpdateNotifier(connections)


async def test_should_send_updated_diagram_to_every_editor_of_the_diagram(
    sut: RealtimeDiagramUpdateNotifier, connections: ConnectionManager
) -> None:
    first, second = make_ws(), make_ws()
    await connections.connect(first, str(DIAGRAM.id), Participant(name="Ana"))
    await connections.connect(second, str(DIAGRAM.id), Participant(name="Bruno"))
    await sut.notify_updated(DIAGRAM, "tab-1")
    expected = {
        "type": "diagram_updated",
        "client_id": "tab-1",
        "diagram": {
            "id": str(DIAGRAM.id),
            "name": "Checkout",
            "folder_id": str(DIAGRAM.folder_id),
            "canvas_state": {"shapes": ["box"]},
            "semantic_metadata": {"shape:1": {"type": "service"}},
            "updated_at": "2026-09-29T12:00:00Z",
        },
    }
    assert sent(first) == [expected]
    assert sent(second) == [expected]


async def test_should_not_leak_share_token(
    sut: RealtimeDiagramUpdateNotifier, connections: ConnectionManager
) -> None:
    ws = make_ws()
    await connections.connect(ws, str(DIAGRAM.id), Participant(name="Guest"))
    await sut.notify_updated(DIAGRAM, None)
    raw_message = cast(AsyncMock, ws.send_text).await_args_list[0].args[0]
    assert "secret-share-token" not in raw_message


async def test_should_send_null_client_id_for_writers_outside_the_editor(
    sut: RealtimeDiagramUpdateNotifier, connections: ConnectionManager
) -> None:
    ws = make_ws()
    await connections.connect(ws, str(DIAGRAM.id), Participant(name="Ana"))
    await sut.notify_updated(DIAGRAM, None)
    assert sent(ws)[0]["client_id"] is None


async def test_should_not_notify_editors_of_other_diagrams(
    sut: RealtimeDiagramUpdateNotifier, connections: ConnectionManager
) -> None:
    other = make_ws()
    await connections.connect(other, str(uuid.uuid4()), Participant(name="Ana"))
    await sut.notify_updated(DIAGRAM, None)
    cast(AsyncMock, other.send_text).assert_not_awaited()
