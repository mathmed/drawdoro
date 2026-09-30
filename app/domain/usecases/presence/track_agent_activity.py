import uuid

from app.domain.constants.presence import AGENT_PRESENCE_SECONDS
from app.domain.contracts.agent_presence import AgentPresence
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.agent_identity import AgentIdentity


class TrackAgentActivityParams(InputData):
    diagram_id: uuid.UUID
    agent: AgentIdentity


# Agents call the API in bursts without a socket, so each call keeps them visible for a while.
class TrackAgentActivity(Usecase[TrackAgentActivityParams, None]):
    def __init__(self, presence: AgentPresence) -> None:
        self._presence = presence

    async def execute(self, params: TrackAgentActivityParams) -> None:
        await self._presence.mark_active(params.diagram_id, params.agent, AGENT_PRESENCE_SECONDS)
