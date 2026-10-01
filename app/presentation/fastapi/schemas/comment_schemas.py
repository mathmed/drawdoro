import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums.revision_origin import RevisionOrigin


class CreateCommentRequest(BaseModel):
    # Omitted or empty for a comment on the whole diagram.
    element_id: str | None = None
    # Plain text; the use case trims it and enforces the length limit.
    content: str
    author_id: uuid.UUID | None = None


class UpdateCommentRequest(BaseModel):
    resolved: bool


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    diagram_id: uuid.UUID
    element_id: str | None
    # Plain text written by a person or an agent: clients must render it as text, never as HTML.
    content: str
    # For agent comments with a personal key, the person the agent works for.
    author_id: uuid.UUID | None
    author_name: str | None
    origin: RevisionOrigin
    agent_name: str | None
    agent_label: str | None
    created_at: datetime
    resolved: bool = Field(validation_alias="is_resolved")
    resolved_at: datetime | None
    resolved_by_id: uuid.UUID | None
    resolved_by_name: str | None
    resolved_by_origin: RevisionOrigin | None
    resolved_by_agent_name: str | None
    resolved_by_agent_label: str | None
    # Whether the caller wrote it; agents may only delete the comments where this is true.
    created_by_you: bool
