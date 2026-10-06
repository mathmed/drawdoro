import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.constants.presence import AGENT_PRESENCE_SECONDS
from app.domain.contracts.agent_presence import AgentPresence
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)
from tests.doubles import double

AGENT = AgentIdentity(id="agent:Claude", name="Claude")
LOCATION = DiagramLocation(workspace_id=uuid.uuid4(), project_id=uuid.uuid4())


@pytest.fixture
def diagrams() -> NonCallableMagicMock:
    repo = double(DiagramRepository)
    repo.get_location.return_value = LOCATION
    return repo


@pytest.fixture
def presence() -> NonCallableMagicMock:
    return double(AgentPresence)


@pytest.fixture
def sut(diagrams: NonCallableMagicMock, presence: NonCallableMagicMock) -> TrackAgentActivity:
    return TrackAgentActivity(diagrams, presence)


async def test_should_keep_agent_visible_for_the_presence_window(
    sut: TrackAgentActivity, diagrams: NonCallableMagicMock, presence: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    await sut.execute(TrackAgentActivityParams(diagram_id=diagram_id, agent=AGENT))
    diagrams.get_location.assert_awaited_once_with(diagram_id)
    presence.mark_active.assert_awaited_once_with(
        diagram_id, LOCATION, AGENT, AGENT_PRESENCE_SECONDS
    )


async def test_should_not_show_an_agent_in_a_diagram_that_does_not_exist(
    sut: TrackAgentActivity, diagrams: NonCallableMagicMock, presence: NonCallableMagicMock
) -> None:
    diagrams.get_location.return_value = None
    await sut.execute(TrackAgentActivityParams(diagram_id=uuid.uuid4(), agent=AGENT))
    presence.mark_active.assert_not_awaited()
