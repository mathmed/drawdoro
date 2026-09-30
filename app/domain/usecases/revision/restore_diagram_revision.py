import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.revision_recorder import RevisionRecorder


class RestoreDiagramRevisionParams(InputData):
    diagram_id: uuid.UUID
    revision_id: uuid.UUID
    author: RevisionAuthor = RevisionAuthor()


# Brings back the canvas and shape metadata of a revision. The diagram keeps its current name and
# folder, and the restore is recorded as a new revision, so it can itself be undone.
class RestoreDiagramRevision(Usecase[RestoreDiagramRevisionParams, Diagram]):
    def __init__(
        self,
        diagrams: DiagramRepository,
        revisions: DiagramRevisionRepository,
        recorder: RevisionRecorder,
        notifier: DiagramUpdateNotifier,
    ) -> None:
        self._diagrams = diagrams
        self._revisions = revisions
        self._recorder = recorder
        self._notifier = notifier

    async def execute(self, params: RestoreDiagramRevisionParams) -> Diagram:
        diagram = await self._diagrams.get_by_id(params.diagram_id)
        if diagram is None:
            raise NotFoundError(f"Diagram {params.diagram_id} not found")
        revision = await self._revisions.get(params.diagram_id, params.revision_id)
        if revision is None or revision.snapshot is None:
            raise NotFoundError(f"Revision {params.revision_id} not found")
        before = DiagramSnapshot.of(diagram)
        diagram.canvas_state = revision.snapshot.canvas_state
        diagram.semantic_metadata = revision.snapshot.semantic_metadata
        updated = await self._diagrams.update(diagram)
        await self._recorder.record(
            updated.id,
            before,
            DiagramSnapshot.of(updated),
            params.author,
            restored_from_id=revision.id,
        )
        # No origin tab: every open editor, the requester's included, must load the restored canvas.
        await self._notifier.notify_updated(updated, None)
        return updated
