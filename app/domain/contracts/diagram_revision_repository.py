import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.models.diagram_revision import DiagramRevision


class DiagramRevisionRepository(ABC):
    @abstractmethod
    async def create(self, revision: DiagramRevision) -> DiagramRevision: ...

    # Replaces the snapshot and updated_at of an existing revision.
    @abstractmethod
    async def update_snapshot(self, revision: DiagramRevision) -> DiagramRevision: ...

    # With its snapshot.
    @abstractmethod
    async def get(
        self, diagram_id: uuid.UUID, revision_id: uuid.UUID
    ) -> DiagramRevision | None: ...

    # With its snapshot.
    @abstractmethod
    async def get_latest(self, diagram_id: uuid.UUID) -> DiagramRevision | None: ...

    # Newest first, without snapshots.
    @abstractmethod
    async def list_by_diagram(self, diagram_id: uuid.UUID, limit: int) -> list[DiagramRevision]: ...

    # Deletes revisions beyond the newest keep_latest, or last updated before older_than. The
    # newest revision is always kept. None disables that rule.
    @abstractmethod
    async def prune(
        self, diagram_id: uuid.UUID, keep_latest: int | None, older_than: datetime | None
    ) -> None: ...
