import uuid

from app.domain.constants.presence import AGENT_PRESENCE_SECONDS
from app.domain.contracts.agent_presence import AgentPresence
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.agent_identity import AgentIdentity


class TrackAgentActivityParams(InputData):
    diagram_id: uuid.UUID
    agent: AgentIdentity


# Agents call the API in bursts without a socket, so each call keeps them visible for a while.
# A diagram that does not exist has nobody to show the agent to.
class TrackAgentActivity(Usecase[TrackAgentActivityParams, None]):
    def __init__(self, diagrams: DiagramRepository, presence: AgentPresence) -> None:
        self._diagrams = diagrams
        self._presence = presence

    async def execute(self, params: TrackAgentActivityParams) -> None:
        location = await self._diagrams.get_location(params.diagram_id)
        if location is None:
            return
        await self._presence.mark_active(
            params.diagram_id, location, params.agent, AGENT_PRESENCE_SECONDS
        )
