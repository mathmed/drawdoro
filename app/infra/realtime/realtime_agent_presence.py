import uuid

from app.domain.contracts.agent_presence import AgentPresence
from app.infra.realtime.connection_manager import ConnectionManager


class RealtimeAgentPresence(AgentPresence):
    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections

    async def mark_active(self, diagram_id: uuid.UUID, agent_name: str, seconds: float) -> None:
        await self._connections.mark_agent_active(str(diagram_id), agent_name, seconds)
