import uuid
from typing import Any

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError


class UpdateDiagramParams(InputData):
    diagram_id: uuid.UUID
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None
    # The editor tab that made the change, so it can skip its own echo; None for other writers.
    origin_client_id: str | None = None


class UpdateDiagram(Usecase[UpdateDiagramParams, Diagram]):
    def __init__(self, repo: DiagramRepository, notifier: DiagramUpdateNotifier) -> None:
        self._repo = repo
        self._notifier = notifier

    async def execute(self, params: UpdateDiagramParams) -> Diagram:
        diagram = await self._repo.get_by_id(params.diagram_id)
        if diagram is None:
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        diagram.name = params.name
        diagram.folder_id = params.folder_id
        diagram.canvas_state = params.canvas_state
        diagram.semantic_metadata = params.semantic_metadata
        updated = await self._repo.update(diagram)
        await self._notifier.notify_updated(updated, params.origin_client_id)
        return updated
