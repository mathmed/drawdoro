import uuid
from datetime import UTC, datetime

from pydantic import Field

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.revision_origin import RevisionOrigin


class Comment(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    diagram_id: uuid.UUID
    # Record id of the shape the comment is anchored to; None for a comment on the whole diagram.
    element_id: str | None = None
    content: str
    # For agents with a personal key, the person the agent works for.
    author_id: uuid.UUID | None = None
    # Read-only projection of the author's current name; not stored on the comment.
    author_name: str | None = None
    origin: RevisionOrigin = RevisionOrigin.HUMAN
    agent_name: str | None = None
    agent_label: str | None = None
    # The personal key an agent used to write the comment; None for people and ownerless agents.
    api_key_id: uuid.UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolved_by_id: uuid.UUID | None = None
    # Read-only projection of the resolver's current name; not stored on the comment.
    resolved_by_name: str | None = None
    resolved_by_origin: RevisionOrigin | None = None
    resolved_by_agent_name: str | None = None
    resolved_by_agent_label: str | None = None
    # Read-only projection: whether whoever asked for the comment is the one who wrote it.
    created_by_you: bool = False

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None
