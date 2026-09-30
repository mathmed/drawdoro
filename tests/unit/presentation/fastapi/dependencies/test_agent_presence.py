import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.user import User
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)
from app.presentation.fastapi.dependencies.agent_presence import (
    AGENT_NAME_MAX_LENGTH,
    get_agent_identity,
    track_agent_activity,
)
from app.presentation.fastapi.dependencies.current_user import Caller

ANA = User(email="ana@example.com", name="Ana")
ANAS_KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_abc", key_hash="hash")


def test_should_accept_agent_name_when_auth_is_disabled() -> None:
    agent = get_agent_identity(x_agent_name="Claude", caller=Caller())
    assert agent == AgentIdentity(id="agent:Claude", name="Claude")


def test_should_accept_ownerless_agent_from_trusted_service() -> None:
    agent = get_agent_identity(x_agent_name="Claude", caller=Caller(is_service=True))
    assert agent == AgentIdentity(id="agent:Claude", name="Claude")


def test_should_tell_agents_apart_by_personal_key() -> None:
    agent = get_agent_identity(x_agent_name="Claude", caller=Caller(user=ANA, api_key=ANAS_KEY))
    assert agent == AgentIdentity(
        id=f"agent:key:{ANAS_KEY.id}",
        name="Claude",
        owner_id=ANA.id,
        owner_name="Ana",
        label="laptop",
    )


def test_should_ignore_agent_name_from_signed_in_people() -> None:
    assert get_agent_identity(x_agent_name="Claude", caller=Caller(user=ANA)) is None


@pytest.mark.parametrize("header", [None, "", "   "])
def test_should_ignore_missing_or_blank_agent_name(header: str | None) -> None:
    assert get_agent_identity(x_agent_name=header, caller=Caller()) is None


def test_should_trim_and_cap_agent_name() -> None:
    agent = get_agent_identity(x_agent_name=f"  {'x' * 100}  ", caller=Caller())
    assert agent is not None
    assert agent.name == "x" * AGENT_NAME_MAX_LENGTH


@pytest.fixture
def use_case() -> TrackAgentActivity:
    return cast(TrackAgentActivity, create_autospec(TrackAgentActivity, instance=True))


async def test_should_track_activity_of_named_agent(use_case: TrackAgentActivity) -> None:
    diagram_id = uuid.uuid4()
    agent = AgentIdentity(id="agent:Claude", name="Claude")
    await track_agent_activity(diagram_id=diagram_id, agent=agent, use_case=use_case)
    cast(AsyncMock, use_case.execute).assert_awaited_once_with(
        TrackAgentActivityParams(diagram_id=diagram_id, agent=agent)
    )


async def test_should_not_track_callers_that_are_not_agents(use_case: TrackAgentActivity) -> None:
    await track_agent_activity(diagram_id=uuid.uuid4(), agent=None, use_case=use_case)
    cast(AsyncMock, use_case.execute).assert_not_awaited()
