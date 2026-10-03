import uuid

from fastapi import Depends, Header

from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.usecases.presence.track_agent_activity import (
    TrackAgentActivity,
    TrackAgentActivityParams,
)
from app.presentation.factories.presence_factories import track_agent_activity_factory
from app.presentation.fastapi.dependencies.current_user import Caller, get_caller

AGENT_NAME_MAX_LENGTH = 40


def get_agent_identity(
    x_agent_name: str | None = Header(default=None),
    caller: Caller = Depends(get_caller),
) -> AgentIdentity | None:
    name = (x_agent_name or "").strip()[:AGENT_NAME_MAX_LENGTH]
    if name == "":
        return None
    return _agent_of(caller, name)


def _agent_of(caller: Caller, name: str) -> AgentIdentity | None:
    # A personal key makes it the agent of that person, told apart from other people's agents.
    if caller.api_key is not None and caller.user is not None:
        return AgentIdentity(
            id=f"agent:key:{caller.api_key.id}",
            name=name,
            owner_id=caller.user.id,
            owner_name=caller.user.name,
            label=caller.api_key.label,
        )
    # Signed-in people calling the API directly can't pose as an agent.
    if caller.user is not None:
        return None
    return AgentIdentity(id=f"agent:{name}", name=name)


async def track_agent_activity(
    diagram_id: uuid.UUID,
    agent: AgentIdentity | None = Depends(get_agent_identity),
    use_case: TrackAgentActivity = Depends(track_agent_activity_factory),
) -> None:
    if agent is None:
        return
    await use_case.execute(TrackAgentActivityParams(diagram_id=diagram_id, agent=agent))
