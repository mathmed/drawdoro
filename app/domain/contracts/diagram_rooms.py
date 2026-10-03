from abc import ABC, abstractmethod

from app.domain.contracts.realtime_connection import RealtimeConnection
from app.domain.entities.objects.participant import Participant


# The editors connected to each diagram: who is in it, and relaying what one sends to the others.
class DiagramRooms(ABC):
    @abstractmethod
    async def connect(
        self, ws: RealtimeConnection, diagram_id: str, participant: Participant
    ) -> None: ...

    @abstractmethod
    def disconnect(self, ws: RealtimeConnection, diagram_id: str) -> None: ...

    @abstractmethod
    def peer_count(self, diagram_id: str) -> int: ...

    @abstractmethod
    async def broadcast(
        self, message: str, diagram_id: str, exclude: RealtimeConnection | None = None
    ) -> None: ...

    # Tells everyone in the diagram who is in it.
    @abstractmethod
    async def broadcast_presence(self, diagram_id: str) -> None: ...
