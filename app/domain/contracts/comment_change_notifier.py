import uuid
from abc import ABC, abstractmethod


# Tells open editors that a diagram's comments changed (e.g. an agent resolved one), so they reload.
class CommentChangeNotifier(ABC):
    @abstractmethod
    async def notify_changed(self, diagram_id: uuid.UUID) -> None: ...
