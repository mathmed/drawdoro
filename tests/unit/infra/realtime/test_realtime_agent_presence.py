import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.infra.realtime.connection_manager import ConnectionManager
from app.infra.realtime.realtime_agent_presence import RealtimeAgentPresence


@pytest.fixture
def connections() -> ConnectionManager:
    return cast(ConnectionManager, create_autospec(ConnectionManager, instance=True))


@pytest.fixture
def sut(connections: ConnectionManager) -> RealtimeAgentPresence:
    return RealtimeAgentPresence(connections)


async def test_should_mark_agent_in_the_diagram_room(
    sut: RealtimeAgentPresence, connections: ConnectionManager
) -> None:
    diagram_id = uuid.uuid4()
    await sut.mark_active(diagram_id, "Claude", 60)
    cast(AsyncMock, connections.mark_agent_active).assert_awaited_once_with(
        str(diagram_id), "Claude", 60
    )
