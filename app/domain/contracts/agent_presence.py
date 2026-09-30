import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.agent_identity import AgentIdentity


class AgentPresence(ABC):
    @abstractmethod
    async def mark_active(
        self, diagram_id: uuid.UUID, agent: AgentIdentity, seconds: float
    ) -> None: ...
