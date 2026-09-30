import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.enums.revision_kind import RevisionKind
from app.domain.enums.revision_origin import RevisionOrigin


class RevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diagram_id: uuid.UUID
    kind: RevisionKind
    origin: RevisionOrigin
    author_id: uuid.UUID | None
    author_name: str | None
    author_picture_url: str | None
    agent_name: str | None
    agent_label: str | None
    summary: str | None
    restored_from_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class RevisionDetailResponse(RevisionResponse):
    name: str
    canvas_state: dict[str, Any] | None
    semantic_metadata: dict[str, Any] | None

    @classmethod
    def from_revision(cls, revision: DiagramRevision) -> RevisionDetailResponse:
        snapshot = revision.snapshot
        return cls.model_validate(
            revision.model_dump()
            | {
                "name": snapshot.name if snapshot else "",
                "canvas_state": snapshot.canvas_state if snapshot else None,
                "semantic_metadata": snapshot.semantic_metadata if snapshot else None,
            }
        )
