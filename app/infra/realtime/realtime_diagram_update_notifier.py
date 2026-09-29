import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.entities.models.diagram import Diagram
from app.infra.realtime.connection_manager import ConnectionManager


class UpdatedDiagram(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    folder_id: uuid.UUID | None
    canvas_state: dict[str, Any] | None
    semantic_metadata: dict[str, Any] | None
    updated_at: datetime


class DiagramUpdatedMessage(BaseModel):
    type: Literal["diagram_updated"] = "diagram_updated"
    client_id: str | None
    diagram: UpdatedDiagram


# Open editors keep their own copy of the diagram and save it back whole, so every persisted
# change is pushed to them; otherwise their next autosave would overwrite it.
class RealtimeDiagramUpdateNotifier(DiagramUpdateNotifier):
    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections

    async def notify_updated(self, diagram: Diagram, origin_client_id: str | None) -> None:
        message = DiagramUpdatedMessage(
            client_id=origin_client_id, diagram=UpdatedDiagram.model_validate(diagram)
        )
        await self._connections.broadcast(message.model_dump_json(), str(diagram.id))
