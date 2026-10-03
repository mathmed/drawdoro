import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.constants.presence import AGENT_PRESENCE_SECONDS
from app.domain.contracts.agent_presence import AgentPresence
from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)
from tests.doubles import double


@pytest.fixture
def presence() -> NonCallableMagicMock:
    return double(AgentPresence)


@pytest.fixture
def sut(presence: NonCallableMagicMock) -> TrackAgentActivity:
    return TrackAgentActivity(presence)


async def test_should_keep_agent_visible_for_the_presence_window(
    sut: TrackAgentActivity, presence: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    agent = AgentIdentity(id="agent:Claude", name="Claude")
    await sut.execute(TrackAgentActivityParams(diagram_id=diagram_id, agent=agent))
    presence.mark_active.assert_awaited_once_with(diagram_id, agent, AGENT_PRESENCE_SECONDS)
