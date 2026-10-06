import uuid
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, SerializerFunctionWrapHandler, model_serializer

from app.domain.entities.objects.diagram_presence import DiagramPresence


class PresenceKind(StrEnum):
    PERSON = "person"
    AGENT = "agent"


class PersonEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    kind: Literal[PresenceKind.PERSON] = PresenceKind.PERSON
    picture_url: str | None


class AgentEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    kind: Literal[PresenceKind.AGENT] = PresenceKind.AGENT
    owner_id: str | None = None
    owner_name: str | None = None
    label: str | None = None

    # Agents on the shared service key have no owner: their entry leaves the owner fields out.
    @model_serializer(mode="wrap")
    def _without_missing_owner(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        fields: dict[str, object] = handler(self)
        return {key: value for key, value in fields.items() if value is not None}


type PresenceEntry = PersonEntry | AgentEntry


# Everyone in the diagram, sent to each of its connections with which entry is them.
class PresenceMessage(BaseModel):
    type: Literal["presence"] = "presence"
    users: list[PresenceEntry]
    you: str
    peers: int


class DiagramPresenceItem(BaseModel):
    diagram_id: str
    project_id: uuid.UUID
    users: list[PresenceEntry]

    @classmethod
    def of(cls, presence: DiagramPresence[PresenceEntry]) -> DiagramPresenceItem:
        return cls(
            diagram_id=presence.diagram_id,
            project_id=presence.project_id,
            users=list(presence.entries),
        )


# What a new sidebar subscriber gets first: every diagram of the workspace someone is in.
class WorkspacePresenceSnapshot(BaseModel):
    type: Literal["presence_snapshot"] = "presence_snapshot"
    you: str | None
    diagrams: list[DiagramPresenceItem]


# Then only the diagrams whose people changed, each with its full list; empty when nobody is left.
class WorkspacePresenceDelta(BaseModel):
    type: Literal["presence_delta"] = "presence_delta"
    diagrams: list[DiagramPresenceItem]
