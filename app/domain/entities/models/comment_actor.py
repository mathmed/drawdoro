import uuid

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.revision_origin import RevisionOrigin


# Who acts on a comment, with the same identity rules as the diagram history: a person, or an
# agent (the MCP server) acting for the owner of a personal key, or without owner on the shared
# service key. api_key_id tells one person's agents apart, so an agent only owns what its key made.
class CommentActor(BaseModel):
    user_id: uuid.UUID | None = None
    origin: RevisionOrigin = RevisionOrigin.HUMAN
    agent_name: str | None = None
    agent_label: str | None = None
    api_key_id: uuid.UUID | None = None

    @property
    def is_agent(self) -> bool:
        return self.origin == RevisionOrigin.AGENT

    # Identifies the actor in logs without personal data or comment text.
    @property
    def audit_label(self) -> str:
        if not self.is_agent:
            return f"user {self.user_id}" if self.user_id is not None else "anonymous user"
        if self.api_key_id is not None:
            return f"agent of user {self.user_id} (key {self.api_key_id})"
        return "ownerless agent"
