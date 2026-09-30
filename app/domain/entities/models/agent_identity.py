import uuid

from app.domain.entities.models.base_model import BaseModel


# An agent shown in a diagram's presence. Agents with a personal key are told apart by key, so
# two people's agents show up as two avatars; the shared service key gives an agent without owner.
class AgentIdentity(BaseModel):
    id: str
    name: str
    owner_id: uuid.UUID | None = None
    owner_name: str | None = None
    label: str | None = None
