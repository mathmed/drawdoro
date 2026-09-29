import re
import uuid
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel
from tools.api import DrawdoroApi, JsonObject

EDITOR_LINK = re.compile(r"/diagrams/(?P<diagram_id>[^/]+)/?$")
# Share tokens come from secrets.token_urlsafe, so anything else is not a Drawdoro link.
SHARE_LINK = re.compile(r"/share/(?P<token>[A-Za-z0-9_-]+)/?$")


class DiagramSummary(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    folder_id: uuid.UUID | None
    name: str
    updated_at: datetime


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
    def __init__(self, api: DrawdoroApi) -> None:
        self._api = api

    def list_diagrams(self, project_id: uuid.UUID) -> list[DiagramSummary]:
        """List the diagrams of a project by id, name and folder, without their content.

        Use get_diagram to read the canvas of one of them.

        Args:
            project_id: Project whose diagrams to list.
        """
        diagrams = self._api.get_list(f"/projects/{project_id}/diagrams")
        return [DiagramSummary.model_validate(diagram) for diagram in diagrams]

    def get_diagram(self, diagram_id: uuid.UUID) -> JsonObject:
        """Get one diagram with its full content.

        canvas_state is a tldraw store snapshot ({"store": {<record id>: <record>}, "schema": ...});
        the text of each shape lives in its props.richText. semantic_metadata maps shape ids to
        architecture metadata (type, label, technology, notes).

        Args:
            diagram_id: Diagram to fetch; in a Drawdoro link it is the part after /diagrams/.
        """
        return self._api.get_object(f"/diagrams/{diagram_id}")

    def open_link(self, url: str) -> JsonObject:
        """Open the diagram behind a Drawdoro link.

        Editor links (https://<host>/diagrams/<diagram_id>) return the same as get_diagram.
        Share links (https://<host>/share/<token>) return a read-only copy without project or
        folder ids, so the diagram cannot be updated through them.

        Args:
            url: Drawdoro link, as copied from the browser or from the Share button.
        """
        path = urlparse(url.strip()).path
        if share := SHARE_LINK.search(path):
            return self._api.get_object(f"/share/{share['token']}")
        editor = EDITOR_LINK.search(path)
        if editor is None:
            raise ToolError(
                f"{url} is not a Drawdoro diagram link (/diagrams/<id> or /share/<token>)"
            )
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
    ) -> JsonObject:
        """Update a diagram. Only the fields you pass change; omitted ones keep their current values.

        People with the diagram open see the change right away.

        Args:
            diagram_id: Diagram to update.
            name: New name for the diagram.
            folder_id: Folder to move the diagram into.
            canvas_state: Complete tldraw store snapshot that replaces the current one. Start from
                get_diagram and send every record back, not only the changed ones; records must
                stay valid tldraw records or the editor may fail to open the diagram.
            semantic_metadata: Complete shape metadata map that replaces the current one.
        """
        # The API's PUT replaces every field, so omitted ones are filled from the current diagram.
        current = StoredDiagram.model_validate(self.get_diagram(diagram_id))
        changes = DiagramChanges(
            name=name,
            folder_id=folder_id,
            canvas_state=canvas_state,
            semantic_metadata=semantic_metadata,
        )
        updated = current.model_copy(update=changes.model_dump(exclude_none=True))
        path = f"/projects/{current.project_id}/diagrams/{diagram_id}"
        return self._api.put(path, updated.model_dump(mode="json", exclude={"project_id"}))
