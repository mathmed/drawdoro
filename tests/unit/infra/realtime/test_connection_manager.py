from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from app.infra.realtime.connection_manager import ConnectionManager


def make_ws() -> WebSocket:
    ws = AsyncMock(spec=WebSocket)
    return cast(WebSocket, ws)


@pytest.fixture
def sut() -> ConnectionManager:
    return ConnectionManager()


async def test_should_accept_and_track_connection(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "diagram-1")
    cast(AsyncMock, ws.accept).assert_awaited_once()
    assert sut.peer_count("diagram-1") == 1


async def test_should_count_peers_per_room(sut: ConnectionManager) -> None:
    await sut.connect(make_ws(), "room-a")
    await sut.connect(make_ws(), "room-a")
    await sut.connect(make_ws(), "room-b")
    assert sut.peer_count("room-a") == 2
    assert sut.peer_count("room-b") == 1


async def test_should_return_zero_for_unknown_room(sut: ConnectionManager) -> None:
    assert sut.peer_count("missing") == 0


async def test_should_remove_connection_and_drop_empty_room(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "room")
    sut.disconnect(ws, "room")
    assert sut.peer_count("room") == 0


async def test_should_broadcast_to_others_excluding_sender(sut: ConnectionManager) -> None:
    sender = make_ws()
    other = make_ws()
    await sut.connect(sender, "room")
    await sut.connect(other, "room")

    await sut.broadcast("hello", "room", exclude=sender)

    cast(AsyncMock, other.send_text).assert_awaited_once_with("hello")
    cast(AsyncMock, sender.send_text).assert_not_awaited()


async def test_should_ignore_broadcast_errors(sut: ConnectionManager) -> None:
    failing = make_ws()
    cast(AsyncMock, failing.send_text).side_effect = RuntimeError("boom")
    healthy = make_ws()
    await sut.connect(failing, "room")
    await sut.connect(healthy, "room")

    await sut.broadcast("payload", "room", exclude=make_ws())

    cast(AsyncMock, healthy.send_text).assert_awaited_once_with("payload")
