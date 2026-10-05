import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.infra.realtime.connection_manager import ConnectionManager
from app.infra.realtime.realtime_agent_presence import RealtimeAgentPresence
from tests.doubles import double


@pytest.fixture
def connections() -> NonCallableMagicMock:
    return double(ConnectionManager)


@pytest.fixture
def sut(connections: NonCallableMagicMock) -> RealtimeAgentPresence:
    return RealtimeAgentPresence(connections)


async def test_should_mark_agent_in_the_diagram_room(
    sut: RealtimeAgentPresence, connections: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    agent = AgentIdentity(id="agent:Claude", name="Claude")
    location = DiagramLocation(workspace_id=uuid.uuid4(), project_id=uuid.uuid4())
    await sut.mark_active(diagram_id, location, agent, 60)
    connections.mark_agent_active.assert_awaited_once_with(str(diagram_id), agent, 60, location)
