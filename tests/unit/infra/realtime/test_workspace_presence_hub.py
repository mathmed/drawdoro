import asyncio
import json
import logging
import uuid
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from app.domain.entities.objects.diagram_location import DiagramLocation
from app.infra.realtime.presence_messages import AgentEntry, PersonEntry
from app.infra.realtime.workspace_presence_hub import WorkspacePresenceHub

BATCH_SECONDS = 0.01
WORKSPACE = uuid.uuid4()
PROJECT = uuid.uuid4()
HERE = DiagramLocation(workspace_id=WORKSPACE, project_id=PROJECT)
ELSEWHERE = DiagramLocation(workspace_id=uuid.uuid4(), project_id=uuid.uuid4())
ANA = PersonEntry(id="user-ana", name="Ana", picture_url="https://example.com/ana.png")
BRUNO = PersonEntry(id="user-bruno", name="Bruno", picture_url=None)
CLAUDE = AgentEntry(id="agent:Claude", name="Claude")


def make_ws() -> WebSocket:
    return cast(WebSocket, AsyncMock(spec=WebSocket))


def sent(ws: WebSocket) -> list[dict[str, object]]:
    return [json.loads(call.args[0]) for call in cast(AsyncMock, ws.send_text).await_args_list]


async def batch_sent() -> None:
    await asyncio.sleep(BATCH_SECONDS * 5)


@pytest.fixture
def sut() -> WorkspacePresenceHub:
    return WorkspacePresenceHub(batch_seconds=BATCH_SECONDS, subscriptions_per_viewer=2)


async def test_should_send_a_new_subscriber_the_workspace_presence(
    sut: WorkspacePresenceHub,
) -> None:
    sut.room_changed("diagram-b", HERE, [ANA, CLAUDE])
    sut.room_changed("diagram-a", HERE, [BRUNO])
    sut.room_changed("diagram-x", ELSEWHERE, [ANA])
    ws = make_ws()

    assert await sut.subscribe(ws, WORKSPACE, "user-ana") is True

    cast(AsyncMock, ws.accept).assert_awaited_once()
    assert sent(ws) == [
        {
            "type": "presence_snapshot",
            "you": "user-ana",
            "diagrams": [
                {
                    "diagram_id": "diagram-a",
                    "project_id": str(PROJECT),
                    "users": [
                        {"id": "user-bruno", "name": "Bruno", "kind": "person", "picture_url": None}
                    ],
                },
                {
                    "diagram_id": "diagram-b",
                    "project_id": str(PROJECT),
                    "users": [
                        {
                            "id": "user-ana",
                            "name": "Ana",
                            "kind": "person",
                            "picture_url": "https://example.com/ana.png",
                        },
                        {"id": "agent:Claude", "name": "Claude", "kind": "agent"},
                    ],
                },
            ],
        }
    ]


async def test_should_batch_changes_into_one_delta_for_the_workspace_only(
    sut: WorkspacePresenceHub,
) -> None:
    member, outsider = make_ws(), make_ws()
    await sut.subscribe(member, WORKSPACE, "user-bruno")
    await sut.subscribe(outsider, ELSEWHERE.workspace_id, "user-zoe")

    sut.room_changed("diagram-a", HERE, [ANA])
    sut.room_changed("diagram-b", HERE, [BRUNO])
    await batch_sent()

    assert sent(member)[1:] == [
        {
            "type": "presence_delta",
            "diagrams": [
                {
                    "diagram_id": "diagram-a",
                    "project_id": str(PROJECT),
                    "users": [ANA.model_dump()],
                },
                {
                    "diagram_id": "diagram-b",
                    "project_id": str(PROJECT),
                    "users": [BRUNO.model_dump()],
                },
            ],
        }
    ]
    assert sent(outsider) == [{"type": "presence_snapshot", "you": "user-zoe", "diagrams": []}]


async def test_should_tell_subscribers_a_diagram_emptied(sut: WorkspacePresenceHub) -> None:
    sut.room_changed("diagram-a", HERE, [ANA])
    ws = make_ws()
    await sut.subscribe(ws, WORKSPACE, None)

    sut.room_changed("diagram-a", HERE, [])
    await batch_sent()

    assert sent(ws)[-1] == {
        "type": "presence_delta",
        "diagrams": [{"diagram_id": "diagram-a", "project_id": str(PROJECT), "users": []}],
    }


async def test_should_send_nothing_for_a_reload(sut: WorkspacePresenceHub) -> None:
    sut.room_changed("diagram-a", HERE, [ANA])
    ws = make_ws()
    await sut.subscribe(ws, WORKSPACE, None)

    sut.room_changed("diagram-a", HERE, [])
    sut.room_changed("diagram-a", HERE, [ANA])
    await batch_sent()

    assert len(sent(ws)) == 1


async def test_should_send_a_later_change_in_a_new_batch(sut: WorkspacePresenceHub) -> None:
    ws = make_ws()
    await sut.subscribe(ws, WORKSPACE, None)

    sut.room_changed("diagram-a", HERE, [ANA])
    await batch_sent()
    sut.room_changed("diagram-a", HERE, [ANA, BRUNO])
    await batch_sent()

    assert [len(message["diagrams"]) for message in sent(ws)[1:]] == [1, 1]  # type: ignore[arg-type]


async def test_should_refuse_a_viewer_over_the_subscription_limit(
    sut: WorkspacePresenceHub,
) -> None:
    first, second, third = make_ws(), make_ws(), make_ws()
    assert await sut.subscribe(first, WORKSPACE, "user-ana") is True
    assert await sut.subscribe(second, ELSEWHERE.workspace_id, "user-ana") is True

    assert await sut.subscribe(third, WORKSPACE, "user-ana") is False
    assert sent(third) == []
    assert await sut.subscribe(make_ws(), WORKSPACE, "user-bruno") is True

    sut.unsubscribe(first, WORKSPACE)
    assert await sut.subscribe(third, WORKSPACE, "user-ana") is True


async def test_should_not_limit_viewers_without_an_identity(sut: WorkspacePresenceHub) -> None:
    results = [await sut.subscribe(make_ws(), WORKSPACE, None) for _ in range(3)]
    assert results == [True, True, True]


async def test_should_stop_sending_to_an_unsubscribed_sidebar(sut: WorkspacePresenceHub) -> None:
    leaving, staying = make_ws(), make_ws()
    await sut.subscribe(leaving, WORKSPACE, "user-ana")
    await sut.subscribe(staying, WORKSPACE, "user-bruno")

    sut.unsubscribe(leaving, WORKSPACE)
    sut.unsubscribe(leaving, WORKSPACE)
    sut.room_changed("diagram-a", HERE, [ANA])
    await batch_sent()

    assert len(sent(leaving)) == 1
    assert len(sent(staying)) == 2


async def test_should_not_batch_changes_nobody_watches(sut: WorkspacePresenceHub) -> None:
    ws = make_ws()
    await sut.subscribe(ws, WORKSPACE, None)
    sut.unsubscribe(ws, WORKSPACE)

    sut.room_changed("diagram-a", HERE, [ANA])

    assert sut._batches == set()


async def test_should_drop_a_sidebar_that_can_no_longer_be_written_to(
    sut: WorkspacePresenceHub,
) -> None:
    dead, alive = make_ws(), make_ws()
    await sut.subscribe(dead, WORKSPACE, "user-ana")
    await sut.subscribe(alive, WORKSPACE, "user-bruno")
    cast(AsyncMock, dead.send_text).side_effect = RuntimeError("gone")

    sut.room_changed("diagram-a", HERE, [ANA])
    await batch_sent()
    sut.room_changed("diagram-a", HERE, [ANA, BRUNO])
    await batch_sent()

    assert cast(AsyncMock, dead.send_text).await_count == 2
    assert len(sent(alive)) == 3
    assert await sut.subscribe(make_ws(), WORKSPACE, "user-ana") is True
    assert await sut.subscribe(make_ws(), WORKSPACE, "user-ana") is True


async def test_should_log_a_batch_that_fails(
    sut: WorkspacePresenceHub, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    await sut.subscribe(make_ws(), WORKSPACE, None)
    broken = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(sut, "_send_batch_later", broken)

    with caplog.at_level(logging.ERROR):
        sut.room_changed("diagram-a", HERE, [ANA])
        await batch_sent()

    assert "workspace presence batch failed" in caplog.text
    assert sut._batches == set()
