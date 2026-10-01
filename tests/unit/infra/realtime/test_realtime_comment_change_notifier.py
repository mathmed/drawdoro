import json
import uuid
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from app.infra.realtime.connection_manager import ConnectionManager, Participant
from app.infra.realtime.realtime_comment_change_notifier import RealtimeCommentChangeNotifier

DIAGRAM_ID = uuid.uuid4()


def make_ws() -> WebSocket:
    return cast(WebSocket, AsyncMock(spec=WebSocket))


def sent(ws: WebSocket) -> list[object]:
    return [json.loads(call.args[0]) for call in cast(AsyncMock, ws.send_text).await_args_list]


@pytest.fixture
def connections() -> ConnectionManager:
    return ConnectionManager()


@pytest.fixture
def sut(connections: ConnectionManager) -> RealtimeCommentChangeNotifier:
    return RealtimeCommentChangeNotifier(connections)


async def test_should_tell_editors_of_the_diagram_without_the_text(
    sut: RealtimeCommentChangeNotifier, connections: ConnectionManager
) -> None:
    editor, elsewhere = make_ws(), make_ws()
    await connections.connect(editor, str(DIAGRAM_ID), Participant(name="Ana"))
    await connections.connect(elsewhere, str(uuid.uuid4()), Participant(name="Bruno"))
    await sut.notify_changed(DIAGRAM_ID)
    assert sent(editor)[-1] == {"type": "comments_changed", "diagram_id": str(DIAGRAM_ID)}
    assert {"type": "comments_changed", "diagram_id": str(DIAGRAM_ID)} not in sent(elsewhere)
