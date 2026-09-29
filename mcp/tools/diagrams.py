import uuid
from typing import Any

from pydantic import BaseModel
from tools.api import DrawdoroApi, JsonObject


class DiagramChanges(BaseModel):
    name: str | None = None
    folder_id: uuid.UUID | None = None
    canvas_state: dict[str, Any] | None = None
    semantic_metadata: dict[str, Any] | None = None


class DiagramUpdate(DiagramChanges):
    name: str


class DiagramTools:
    def __init__(self, api: DrawdoroApi) -> None:
        self._api = api

    def list_diagrams(self, project_id: uuid.UUID) -> list[JsonObject]:
        """List the diagrams of a project, each with its canvas_state and semantic_metadata.

        This returns every canvas in the project; prefer get_diagram when you need only one.

        Args:
            project_id: Project whose diagrams to list.
        """
        return self._api.get_list(f"/projects/{project_id}/diagrams")

    def get_diagram(self, project_id: uuid.UUID, diagram_id: uuid.UUID) -> JsonObject:
        """Get one diagram with its full content.

        canvas_state is a tldraw store snapshot ({"store": {<record id>: <record>}, "schema": ...});
        the text of each shape lives in its props.richText. semantic_metadata maps shape ids to
        architecture metadata (type, label, technology, notes).

        Args:
            project_id: Project that owns the diagram.
            diagram_id: Diagram to fetch.
        """
        return self._api.get_object(_diagram_path(project_id, diagram_id))

    def update_diagram(
        self,
        project_id: uuid.UUID,
        diagram_id: uuid.UUID,
        name: str | None = None,
        folder_id: uuid.UUID | None = None,
        canvas_state: dict[str, Any] | None = None,
        semantic_metadata: dict[str, Any] | None = None,
    ) -> JsonObject:
        """Update a diagram. Only the fields you pass change; omitted ones keep their current values.

        People with the diagram open see the change right away.

        Args:
            project_id: Project that owns the diagram.
            diagram_id: Diagram to update.
            name: New name for the diagram.
            folder_id: Folder to move the diagram into.
            canvas_state: Complete tldraw store snapshot that replaces the current one. Start from
                get_diagram and send every record back, not only the changed ones; records must
                stay valid tldraw records or the editor may fail to open the diagram.
            semantic_metadata: Complete shape metadata map that replaces the current one.
        """
        # The API's PUT replaces every field, so omitted ones are filled from the current diagram.
        path = _diagram_path(project_id, diagram_id)
        current = DiagramUpdate.model_validate(self._api.get_object(path))
        changes = DiagramChanges(
            name=name,
            folder_id=folder_id,
            canvas_state=canvas_state,
            semantic_metadata=semantic_metadata,
        )
        updated = current.model_copy(update=changes.model_dump(exclude_none=True))
        return self._api.put(path, updated.model_dump(mode="json"))


def _diagram_path(project_id: uuid.UUID, diagram_id: uuid.UUID) -> str:
    return f"/projects/{project_id}/diagrams/{diagram_id}"
