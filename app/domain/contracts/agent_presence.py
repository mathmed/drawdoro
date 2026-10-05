import uuid
from abc import ABC, abstractmethod

from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.objects.diagram_location import DiagramLocation


class AgentPresence(ABC):
    @abstractmethod
    async def mark_active(
        self,
        diagram_id: uuid.UUID,
        location: DiagramLocation,
        agent: AgentIdentity,
        seconds: float,
    ) -> None: ...
