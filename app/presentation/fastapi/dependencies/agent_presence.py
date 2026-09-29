import uuid

from fastapi import Depends, Header

from app.common.settings import Settings, get_settings
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)
from app.presentation.factories.presence_factories import track_agent_activity_factory
from app.presentation.fastapi.dependencies.current_user import is_service_request

AGENT_NAME_MAX_LENGTH = 40


def get_agent_name(
    x_agent_name: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> str | None:
    name = (x_agent_name or "").strip()[:AGENT_NAME_MAX_LENGTH]
    # Only trusted services may show up as an agent; otherwise any user could pose as one.
    if name == "" or (settings.auth_enabled and not is_service_request(x_api_key, settings)):
        return None
    return name


async def track_agent_activity(
    diagram_id: uuid.UUID,
    agent_name: str | None = Depends(get_agent_name),
    use_case: TrackAgentActivity = Depends(track_agent_activity_factory),
) -> None:
    if agent_name is None:
        return
    await use_case.execute(TrackAgentActivityParams(diagram_id=diagram_id, agent_name=agent_name))
