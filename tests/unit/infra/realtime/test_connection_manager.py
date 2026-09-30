import asyncio
import json
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from app.infra.realtime.connection_manager import ConnectionManager, Participant

ANA = Participant(name="Ana", user_id="user-ana")
BRUNO = Participant(name="Bruno", user_id="user-bruno")


def make_ws() -> WebSocket:
    return cast(WebSocket, AsyncMock(spec=WebSocket))


def sent(ws: WebSocket) -> list[dict[str, object]]:
    return [json.loads(call.args[0]) for call in cast(AsyncMock, ws.send_text).await_args_list]


@pytest.fixture
def sut() -> ConnectionManager:
    return ConnectionManager()


async def test_should_accept_and_track_connection(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "diagram-1", ANA)
    cast(AsyncMock, ws.accept).assert_awaited_once()
    assert sut.peer_count("diagram-1") == 1


async def test_should_count_people_not_tabs(sut: ConnectionManager) -> None:
    await sut.connect(make_ws(), "room", ANA)
    await sut.connect(make_ws(), "room", Participant(name="Ana", user_id="user-ana"))
    await sut.connect(make_ws(), "room", BRUNO)
    assert sut.participants("room") == [
        {"id": "user-ana", "name": "Ana", "kind": "person", "picture_url": None},
        {"id": "user-bruno", "name": "Bruno", "kind": "person", "picture_url": None},
    ]


async def test_should_count_each_guest_connection(sut: ConnectionManager) -> None:
    await sut.connect(make_ws(), "room", Participant(name="Guest"))
    await sut.connect(make_ws(), "room", Participant(name="Guest"))
    assert sut.peer_count("room") == 2


async def test_should_return_zero_for_unknown_room(sut: ConnectionManager) -> None:
    assert sut.peer_count("missing") == 0


async def test_should_remove_connection_and_drop_empty_room(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "room", ANA)
    sut.disconnect(ws, "room")
    assert sut.peer_count("room") == 0


async def test_should_broadcast_to_everyone_but_sender(sut: ConnectionManager) -> None:
    sender, other = make_ws(), make_ws()
    await sut.connect(sender, "room", ANA)
    await sut.connect(other, "room", BRUNO)
    await sut.broadcast("hello", "room", exclude=sender)
    cast(AsyncMock, other.send_text).assert_awaited_once_with("hello")
    cast(AsyncMock, sender.send_text).assert_not_awaited()


async def test_should_drop_sockets_that_fail_to_receive(sut: ConnectionManager) -> None:
    failing, healthy, sender = make_ws(), make_ws(), make_ws()
    cast(AsyncMock, failing.send_text).side_effect = RuntimeError("gone")
    await sut.connect(failing, "room", ANA)
    await sut.connect(healthy, "room", BRUNO)
    await sut.connect(sender, "room", Participant(name="Carla", user_id="user-carla"))
    await sut.broadcast("hello", "room", exclude=sender)
    cast(AsyncMock, healthy.send_text).assert_awaited_once_with("hello")
    assert [p["id"] for p in sut.participants("room")] == ["user-bruno", "user-carla"]


async def test_should_tell_each_connection_who_is_online_and_who_they_are(
    sut: ConnectionManager,
) -> None:
    ana_ws, bruno_ws = make_ws(), make_ws()
    await sut.connect(ana_ws, "room", ANA)
    await sut.connect(bruno_ws, "room", BRUNO)
    await sut.broadcast_presence("room")
    ana_message = sent(ana_ws)[-1]
    assert ana_message["type"] == "presence"
    assert ana_message["you"] == "user-ana"
    assert ana_message["peers"] == 2
    assert sent(bruno_ws)[-1]["you"] == "user-bruno"


async def test_should_announce_again_after_dropping_a_dead_socket(sut: ConnectionManager) -> None:
    dead, alive = make_ws(), make_ws()
    cast(AsyncMock, dead.send_text).side_effect = RuntimeError("gone")
    await sut.connect(dead, "room", ANA)
    await sut.connect(alive, "room", BRUNO)
    await sut.broadcast_presence("room")
    assert sent(alive)[-1]["users"] == [
        {"id": "user-bruno", "name": "Bruno", "kind": "person", "picture_url": None}
    ]


CLAUDE = {"id": "agent:Claude", "name": "Claude", "kind": "agent"}


def last_presence_users(ws: WebSocket) -> list[dict[str, str]]:
    return cast(list[dict[str, str]], sent(ws)[-1]["users"])


async def test_should_list_active_agent_after_people(sut: ConnectionManager) -> None:
    await sut.connect(make_ws(), "room", BRUNO)
    await sut.mark_agent_active("room", "Claude", seconds=60)
    assert sut.participants("room") == [
        {"id": "user-bruno", "name": "Bruno", "kind": "person", "picture_url": None},
        CLAUDE,
    ]


async def test_should_announce_agent_when_it_arrives(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "room", ANA)
    await sut.mark_agent_active("room", "Claude", seconds=60)
    assert CLAUDE in last_presence_users(ws)


async def test_should_not_announce_agent_again_while_it_is_listed(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "room", ANA)
    await sut.mark_agent_active("room", "Claude", seconds=60)
    await sut.mark_agent_active("room", "Claude", seconds=60)
    assert len(sent(ws)) == 1


async def test_should_remove_agent_when_it_goes_quiet(sut: ConnectionManager) -> None:
    ws = make_ws()
    await sut.connect(ws, "room", ANA)
    await sut.mark_agent_active("room", "Claude", seconds=0.01)
    await asyncio.sleep(0.05)
    assert CLAUDE not in sut.participants("room")
    assert CLAUDE not in last_presence_users(ws)


async def test_should_keep_agent_listed_while_it_stays_active(sut: ConnectionManager) -> None:
    await sut.mark_agent_active("room", "Claude", seconds=0.1)
    await asyncio.sleep(0.06)
    await sut.mark_agent_active("room", "Claude", seconds=0.1)
    await asyncio.sleep(0.06)
    assert sut.participants("room") == [CLAUDE]


async def test_should_share_profile_photo_in_presence(sut: ConnectionManager) -> None:
    photo = "https://lh3.googleusercontent.com/a/ana"
    ws = make_ws()
    await sut.connect(ws, "room", Participant(name="Ana", user_id="user-ana", picture_url=photo))
    await sut.broadcast_presence("room")
    assert sent(ws)[-1]["users"] == [
        {"id": "user-ana", "name": "Ana", "kind": "person", "picture_url": photo}
    ]
