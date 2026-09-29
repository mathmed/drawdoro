import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.constants.presence import AGENT_PRESENCE_SECONDS
from app.domain.contracts.agent_presence import AgentPresence
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)


@pytest.fixture
def presence() -> AgentPresence:
    return cast(AgentPresence, create_autospec(AgentPresence))


@pytest.fixture
def sut(presence: AgentPresence) -> TrackAgentActivity:
    return TrackAgentActivity(presence)


async def test_should_keep_agent_visible_for_the_presence_window(
    sut: TrackAgentActivity, presence: AgentPresence
) -> None:
    diagram_id = uuid.uuid4()
    await sut.execute(TrackAgentActivityParams(diagram_id=diagram_id, agent_name="Claude"))
    cast(AsyncMock, presence.mark_active).assert_awaited_once_with(
        diagram_id, "Claude", AGENT_PRESENCE_SECONDS
    )
