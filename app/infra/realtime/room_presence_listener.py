from abc import ABC, abstractmethod

from app.domain.entities.objects.diagram_location import DiagramLocation
from app.infra.realtime.presence_messages import PresenceEntry


# Told whenever the people (or agents) in a located diagram room change.
class RoomPresenceListener(ABC):
    @abstractmethod
    def room_changed(
        self, diagram_id: str, location: DiagramLocation, entries: list[PresenceEntry]
    ) -> None: ...
