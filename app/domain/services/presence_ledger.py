import uuid
from collections.abc import Sequence

from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.entities.objects.diagram_presence import DiagramPresence


# Who is in each diagram, grouped by workspace, and which changes the workspace's subscribers have
# not been told yet. Changes are collected per workspace and taken as one batch; a diagram that
# ends the batch as it started (someone reloading the page) is left out of it.
class PresenceLedger[Entry]:
    def __init__(self) -> None:
        self._current: dict[str, DiagramPresence[Entry]] = {}
        self._diagrams_by_workspace: dict[uuid.UUID, set[str]] = {}
        # What the subscribers were last told, per diagram; a diagram nobody is in is absent.
        self._published: dict[str, tuple[Entry, ...]] = {}
        self._pending: dict[uuid.UUID, dict[str, uuid.UUID]] = {}

    # True when the change starts a new batch for the workspace: the caller takes it later, once.
    # Without subscribers there is nobody to tell, so the change counts as told right away.
    def record(
        self,
        diagram_id: str,
        location: DiagramLocation,
        entries: Sequence[Entry],
        watched: bool,
    ) -> bool:
        self._store(DiagramPresence(diagram_id, location.project_id, tuple(entries)), location)
        if not watched:
            self._publish(diagram_id, tuple(entries))
            return False
        pending = self._pending.setdefault(location.workspace_id, {})
        starts_batch = pending == {}
        pending[diagram_id] = location.project_id
        return starts_batch

    def snapshot(self, workspace_id: uuid.UUID) -> list[DiagramPresence[Entry]]:
        diagram_ids = sorted(self._diagrams_by_workspace.get(workspace_id, set()))
        return [self._current[diagram_id] for diagram_id in diagram_ids]

    def take_changes(self, workspace_id: uuid.UUID) -> list[DiagramPresence[Entry]]:
        changes: list[DiagramPresence[Entry]] = []
        for diagram_id, project_id in sorted(self._pending.pop(workspace_id, {}).items()):
            current = self._current.get(diagram_id)
            entries = current.entries if current is not None else ()
            if entries == self._published.get(diagram_id, ()):
                continue
            self._publish(diagram_id, entries)
            changes.append(DiagramPresence(diagram_id, project_id, entries))
        return changes

    def _store(self, presence: DiagramPresence[Entry], location: DiagramLocation) -> None:
        diagram_ids = self._diagrams_by_workspace.setdefault(location.workspace_id, set())
        if presence.entries:
            self._current[presence.diagram_id] = presence
            diagram_ids.add(presence.diagram_id)
            return
        self._current.pop(presence.diagram_id, None)
        diagram_ids.discard(presence.diagram_id)
        if not diagram_ids:
            del self._diagrams_by_workspace[location.workspace_id]

    def _publish(self, diagram_id: str, entries: tuple[Entry, ...]) -> None:
        if entries:
            self._published[diagram_id] = entries
        else:
            self._published.pop(diagram_id, None)
