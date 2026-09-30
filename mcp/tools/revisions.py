import uuid
from enum import StrEnum

from pydantic import BaseModel
from tools.api import BackendApi
from tools.diagrams import UtcDatetime

DEFAULT_LISTED_REVISIONS = 20
MAX_LISTED_REVISIONS = 200


class RevisionKind(StrEnum):
    EDIT = "edit"
    RESTORE = "restore"
    BASELINE = "baseline"


class RevisionOrigin(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class Revision(BaseModel):
    id: uuid.UUID
    kind: RevisionKind
    origin: RevisionOrigin
    author_name: str | None
    agent_name: str | None
    agent_label: str | None
    summary: str | None
    restored_from_id: uuid.UUID | None
    created_at: UtcDatetime
    updated_at: UtcDatetime


class RestoredDiagram(BaseModel):
    id: uuid.UUID
    name: str
    updated_at: UtcDatetime
    restored_from_id: uuid.UUID


class RevisionTools:
    def __init__(self, api: BackendApi) -> None:
        self._api = api

    def list_revisions(
        self, diagram_id: uuid.UUID, limit: int = DEFAULT_LISTED_REVISIONS
    ) -> list[Revision]:
        """List the history of a diagram, newest first, without the saved canvases.

        Each revision says who made it: origin "human" is a person in the editor (author_name),
        "agent" is an agent such as you (agent_name, with author_name as the person it works for
        and agent_label as the name of their key). kind "baseline" is the state found before the
        first recorded change, "restore" a revision brought back. A person's saves within a few
        minutes share one revision, and old revisions are deleted after a while.

        Args:
            diagram_id: Diagram whose history to list.
            limit: How many revisions to return, newest first (1 to 200).
        """
        count = max(1, min(limit, MAX_LISTED_REVISIONS))
        revisions = self._api.get_list(f"/diagrams/{diagram_id}/revisions?limit={count}")
        return [Revision.model_validate(revision) for revision in revisions]

    def restore_revision(self, diagram_id: uuid.UUID, revision_id: uuid.UUID) -> RestoredDiagram:
        """Bring a diagram's canvas and shape metadata back to how they were in a revision.

        The name and folder stay as they are. The restore is recorded as a new revision, so it
        can be undone by restoring the revision listed right before it, and people with the
        diagram open see it right away. Ask the user before restoring over other people's work.

        Args:
            diagram_id: Diagram to restore.
            revision_id: Revision to bring back, from list_revisions.
        """
        saved = self._api.post(f"/diagrams/{diagram_id}/revisions/{revision_id}/restore", {})
        return RestoredDiagram.model_validate(saved | {"restored_from_id": revision_id})
