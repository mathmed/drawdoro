import uuid

from app.domain.entities.models.base_model import BaseModel
from app.domain.enums.revision_origin import RevisionOrigin


# Who made a change: a person in the editor, or an agent (the MCP server) acting for its owner.
# For agents with a personal key, user_id, name and picture_url describe the owner.
class RevisionAuthor(BaseModel):
    user_id: uuid.UUID | None = None
    name: str | None = None
    picture_url: str | None = None
    origin: RevisionOrigin = RevisionOrigin.HUMAN
    agent_name: str | None = None
    agent_label: str | None = None
