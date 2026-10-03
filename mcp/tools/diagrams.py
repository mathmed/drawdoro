import re
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any
from urllib.parse import urlparse

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import AfterValidator, BaseModel
from tools.api import BackendApi, JsonObject
from tools.canvas import Canvas, ShapeOutline

EDITOR_LINK = re.compile(r"/diagrams/(?P<diagram_id>[^/]+)/?$")
# Share tokens come from secrets.token_urlsafe, so anything else is not a diagram link.
# The API rejects longer history summaries.
REVISION_SUMMARY_MAX_LENGTH = 500
SHARE_LINK = re.compile(r"/share/(?P<token>[A-Za-z0-9_-]+)/?$")


def _assume_utc(value: datetime) -> datetime:
    # The API sends naive timestamps; without an offset they are not valid JSON Schema date-times.
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_assume_utc)]


class DiagramSummary(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    folder_id: uuid.UUID | None
    name: str
    updated_at: UtcDatetime


class DiagramSaved(BaseModel):
    id: uuid.UUID
    name: str
    updated_at: UtcDatetime
    records: int


class ShapeEdits(DiagramSaved):
    created: list[str]
    changed: list[str]
    deleted: list[str]


class DiagramOutline(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    updated_at: UtcDatetime
    shapes: list[ShapeOutline]


class NewDiagram(BaseModel):
    name: str
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None


class DiagramChanges(BaseModel):
    name: str | None = None
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None


class DiagramUpdate(DiagramChanges):
    name: str


class StoredDiagram(DiagramUpdate):
    project_id: uuid.UUID


class DiagramTools:
    def __init__(self, api: BackendApi) -> None:
        self._api = api

    def list_diagrams(self, project_id: uuid.UUID) -> list[DiagramSummary]:
        """List the diagrams of a project by id, name and folder, without their content.

        Use get_diagram_outline or get_diagram to read the canvas of one of them.

        Args:
            project_id: Project whose diagrams to list.
        """
        diagrams = self._api.get_list(f"/projects/{project_id}/diagrams")
        return [DiagramSummary.model_validate(diagram) for diagram in diagrams]

    def get_diagram(self, diagram_id: uuid.UUID) -> JsonObject:
        """Get one diagram with its full content.

        canvas_state is a tldraw store snapshot ({"store": {<record id>: <record>}, "schema": ...});
        the text of each shape lives in its props.richText. semantic_metadata maps shape ids to
        architecture metadata (type, label, technology, notes). The snapshot is large: to find
        shapes and read their text, get_diagram_outline is much smaller.

        Args:
            diagram_id: Diagram to fetch; in an editor link it is the part after /diagrams/.
        """
        return self._api.get_object(f"/diagrams/{diagram_id}")

    def get_diagram_outline(self, diagram_id: uuid.UUID) -> DiagramOutline:
        """Get a compact outline of a diagram: every shape with its position, size, colour and text.

        Shapes come in reading order (top to bottom, then left to right) with rounded coordinates
        and plain text; fields a shape does not have are left out. Arrows name the shapes they
        connect in start and end. Use it to find the ids to pass to edit_shapes and
        render_diagram, and get_diagram when you need the exact tldraw records.

        Args:
            diagram_id: Diagram to outline.
        """
        diagram = self.get_diagram(diagram_id)
        summary = DiagramSummary.model_validate(diagram)
        return DiagramOutline(
            id=summary.id,
            project_id=summary.project_id,
            name=summary.name,
            updated_at=summary.updated_at,
            shapes=Canvas(diagram.get("canvas_state")).outline(),
        )

    def open_link(self, url: str) -> JsonObject:
        """Open the diagram behind an editor or share link.

        Editor links (https://<host>/diagrams/<diagram_id>) return the same as get_diagram.
        Share links (https://<host>/share/<token>) return a read-only copy without project or
        folder ids, so the diagram cannot be updated through them.

        Args:
            url: Diagram link, as copied from the browser or from the Share button.
        """
        path = urlparse(url.strip()).path
        if share := SHARE_LINK.search(path):
            return self._api.get_object(f"/share/{share['token']}")
        editor = EDITOR_LINK.search(path)
        if editor is None:
            raise ToolError(f"{url} is not a diagram link (/diagrams/<id> or /share/<token>)")
        try:
            diagram_id = uuid.UUID(editor["diagram_id"])
        except ValueError as exc:
            raise ToolError(f"{url} does not contain a valid diagram id") from exc
        return self.get_diagram(diagram_id)

    def create_diagram(
        self,
        project_id: uuid.UUID,
        name: str,
        folder_id: uuid.UUID | None = None,
        canvas_state: dict[str, Any] | None = None,
    ) -> JsonObject:
        """Create a diagram in a project.

        The link to open it is https://<host>/diagrams/<id of the created diagram>.

        Args:
            project_id: Project that will own the diagram.
            name: Diagram name.
            folder_id: Folder to create it in; omit for the project root.
            canvas_state: Initial tldraw store snapshot; omit for an empty canvas.
        """
        body = NewDiagram(name=name, folder_id=folder_id, canvas_state=canvas_state)
        return self._api.post(f"/projects/{project_id}/diagrams", body.model_dump(mode="json"))

    def update_diagram(
        self,
        diagram_id: uuid.UUID,
        name: str | None = None,
        folder_id: uuid.UUID | None = None,
        canvas_state: dict[str, Any] | None = None,
        semantic_metadata: dict[str, Any] | None = None,
        summary: str | None = None,
    ) -> DiagramSaved:
        """Update a diagram. Only the fields you pass change; omitted ones keep their current values.

        People with the diagram open see the change right away. To change only some shapes,
        prefer edit_shapes: it sends those records instead of the whole canvas.

        Args:
            diagram_id: Diagram to update.
            name: New name for the diagram.
            folder_id: Folder to move the diagram into.
            canvas_state: Complete tldraw store snapshot that replaces the current one. Start from
                get_diagram and send every record back, not only the changed ones; records must
                stay valid tldraw records or the editor may fail to open the diagram.
            semantic_metadata: Complete shape metadata map that replaces the current one.
            summary: One sentence on what you changed and why, shown in the diagram's history
                next to your change (e.g. "Added the payment queue between API and worker").
        """
        # The API's PUT replaces every field, so omitted ones are filled from the current diagram.
        current = StoredDiagram.model_validate(self.get_diagram(diagram_id))
        changes = DiagramChanges(
            name=name,
            folder_id=folder_id,
            canvas_state=canvas_state,
            semantic_metadata=semantic_metadata,
        )
        given = changes.model_dump(exclude_none=True)
        updated = current.model_copy(update=given)
        saved = self._save(
            diagram_id, updated, summary or f"Updated {', '.join(given) or 'nothing'}"
        )
        store = (updated.canvas_state or {}).get("store", {})
        return DiagramSaved.model_validate(saved | {"records": len(store)})

    def edit_shapes(
        self,
        diagram_id: uuid.UUID,
        upsert: list[dict[str, Any]] | None = None,
        delete: list[str] | None = None,
        expected_updated_at: datetime | None = None,
        summary: str | None = None,
    ) -> ShapeEdits:
        """Create, change or delete some records of a diagram without sending the whole canvas.

        Deletions run first, so deleting an id and upserting it again replaces that record whole.
        People with the diagram open see the change right away. Check the result with
        render_diagram.

        Before drawing a logo, an icon or a component the user may have saved, look for it with
        list_gallery_items and place it with insert_gallery_item instead.

        Args:
            diagram_id: Diagram to edit.
            upsert: tldraw records to create or change, each with its "id". An id already in the
                diagram is changed with JSON Merge Patch: objects merge key by key, null removes a
                key, lists and plain values replace the stored ones. So {"id": "shape:a",
                "props": {"w": 200}} only changes the width, and {"id": "shape:a", "meta":
                {"fontSize": 20}} only the label size. A new shape needs its "type" and complete
                "props" (copy them from an existing shape of the same type); typeName, parentId
                (the first page), index (above every shape), x, y, rotation, isLocked, opacity and
                meta are filled in when missing. Any other new record must be complete.
            delete: Ids of records to delete. Deleting a shape also deletes the shapes inside it
                and the arrow bindings attached to it.
            expected_updated_at: updated_at of the diagram when you read it. If it was saved after
                that, nothing changes and the call fails, so you can read it again first.
            summary: One sentence on what you changed and why, shown in the diagram's history
                next to your change (e.g. "Renamed the auth service and linked it to the DB").
        """
        _require_edits(upsert, delete)
        diagram = self.get_diagram(diagram_id)
        _check_not_stale(DiagramSummary.model_validate(diagram).updated_at, expected_updated_at)
        current = StoredDiagram.model_validate(diagram)
        canvas = Canvas(current.canvas_state)
        deleted = canvas.delete(delete or [])
        created, changed = canvas.upsert(upsert or [])
        saved = self._save(
            diagram_id,
            current.model_copy(update={"canvas_state": canvas.to_snapshot()}),
            summary or _describe_edits(created, changed, deleted),
        )
        return ShapeEdits.model_validate(
            saved
            | {
                "records": canvas.record_count(),
                "created": created,
                "changed": changed,
                "deleted": deleted,
            }
        )

    def _save(self, diagram_id: uuid.UUID, diagram: StoredDiagram, summary: str) -> JsonObject:
        path = f"/projects/{diagram.project_id}/diagrams/{diagram_id}"
        body = diagram.model_dump(mode="json", exclude={"project_id"})
        saved = self._api.put(
            path, body | {"revision_summary": summary[:REVISION_SUMMARY_MAX_LENGTH]}
        )
        # Echoing the saved canvas back would cost the agent as much as sending it.
        return {key: saved[key] for key in ("id", "name", "updated_at")}


def _describe_edits(created: list[str], changed: list[str], deleted: list[str]) -> str:
    counts = {"created": len(created), "changed": len(changed), "deleted": len(deleted)}
    done = [f"{count} {verb}" for verb, count in counts.items() if count]
    return f"Edited the canvas: {', '.join(done) or 'no records'}"


def _require_edits(upsert: list[dict[str, Any]] | None, delete: list[str] | None) -> None:
    if not upsert and not delete:
        raise ToolError("Pass the records to upsert, the ids to delete, or both")


def _check_not_stale(updated_at: datetime, expected_updated_at: datetime | None) -> None:
    if expected_updated_at is not None and updated_at != _assume_utc(expected_updated_at):
        raise ToolError(
            f"The diagram was saved at {updated_at.isoformat()}, after the version you read; "
            "read it again before editing"
        )
