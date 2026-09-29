import uuid
from abc import ABC, abstractmethod


class AgentPresence(ABC):
    @abstractmethod
    async def mark_active(self, diagram_id: uuid.UUID, agent_name: str, seconds: float) -> None: ...
