import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.common.settings import Settings
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)
from app.presentation.fastapi.dependencies.agent_presence import (
    AGENT_NAME_MAX_LENGTH,
    get_agent_name,
    track_agent_activity,
)

AUTH_OFF = Settings(auth_enabled=False)
AUTH_ON = Settings(auth_enabled=True, service_api_key="svc-key")


def test_should_accept_agent_name_when_auth_is_disabled() -> None:
    assert get_agent_name(x_agent_name="Claude", x_api_key=None, settings=AUTH_OFF) == "Claude"


def test_should_accept_agent_name_from_trusted_service() -> None:
    assert get_agent_name(x_agent_name="Claude", x_api_key="svc-key", settings=AUTH_ON) == "Claude"


@pytest.mark.parametrize("api_key", [None, "wrong-key"])
def test_should_ignore_agent_name_from_untrusted_callers(api_key: str | None) -> None:
    assert get_agent_name(x_agent_name="Claude", x_api_key=api_key, settings=AUTH_ON) is None


@pytest.mark.parametrize("header", [None, "", "   "])
def test_should_ignore_missing_or_blank_agent_name(header: str | None) -> None:
    assert get_agent_name(x_agent_name=header, x_api_key=None, settings=AUTH_OFF) is None


def test_should_trim_and_cap_agent_name() -> None:
    name = get_agent_name(x_agent_name=f"  {'x' * 100}  ", x_api_key=None, settings=AUTH_OFF)
    assert name == "x" * AGENT_NAME_MAX_LENGTH


@pytest.fixture
def use_case() -> TrackAgentActivity:
    return cast(TrackAgentActivity, create_autospec(TrackAgentActivity, instance=True))


async def test_should_track_activity_of_named_agent(use_case: TrackAgentActivity) -> None:
    diagram_id = uuid.uuid4()
    await track_agent_activity(diagram_id=diagram_id, agent_name="Claude", use_case=use_case)
    cast(AsyncMock, use_case.execute).assert_awaited_once_with(
        TrackAgentActivityParams(diagram_id=diagram_id, agent_name="Claude")
    )


async def test_should_not_track_callers_that_are_not_agents(use_case: TrackAgentActivity) -> None:
    await track_agent_activity(diagram_id=uuid.uuid4(), agent_name=None, use_case=use_case)
    cast(AsyncMock, use_case.execute).assert_not_awaited()
