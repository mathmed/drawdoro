import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.enums.revision_kind import RevisionKind
from app.domain.enums.revision_origin import RevisionOrigin


class DiagramRevision(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    diagram_id: uuid.UUID
    kind: RevisionKind = RevisionKind.EDIT
    origin: RevisionOrigin = RevisionOrigin.HUMAN
    author_id: uuid.UUID | None = None
    # The author's profile when the change was made, so the history survives renames and removals.
    author_name: str | None = None
    author_picture_url: str | None = None
    agent_name: str | None = None
    agent_label: str | None = None
    summary: str | None = None
    restored_from_id: uuid.UUID | None = None
    # Left out when revisions are listed, so the list stays small.
    snapshot: DiagramSnapshot | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # When the snapshot was last replaced: a person's edits within the interval share one revision.
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
