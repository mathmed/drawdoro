from abc import ABC, abstractmethod

from app.domain.entities.models.diagram import Diagram


class DiagramUpdateNotifier(ABC):
    @abstractmethod
    async def notify_updated(self, diagram: Diagram, origin_client_id: str | None) -> None: ...
