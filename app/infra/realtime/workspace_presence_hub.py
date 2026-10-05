import asyncio
import logging
import uuid
from collections import Counter

from app.domain.constants.presence import (
    WORKSPACE_PRESENCE_BATCH_SECONDS,
    WORKSPACE_PRESENCE_SUBSCRIPTIONS_PER_USER,
)
from app.domain.contracts.realtime_connection import RealtimeConnection
from app.domain.contracts.workspace_presence import WorkspacePresence
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.services.presence_ledger import PresenceLedger
from app.infra.realtime.presence_messages import (
    DiagramPresenceItem,
    PresenceEntry,
    WorkspacePresenceDelta,
    WorkspacePresenceSnapshot,
)
from app.infra.realtime.room_presence_listener import RoomPresenceListener

logger = logging.getLogger(__name__)


# Fans the diagram rooms' presence out to the sidebars subscribed to each workspace: a snapshot on
# subscribe, then one batched delta per workspace at most every `batch_seconds`. Nothing is stored
# beyond memory, and only the workspace's own diagrams ever reach its subscribers.
class WorkspacePresenceHub(WorkspacePresence, RoomPresenceListener):
    def __init__(self, batch_seconds: float, subscriptions_per_viewer: int) -> None:
        self._batch_seconds = batch_seconds
        self._subscriptions_per_viewer = subscriptions_per_viewer
        self._ledger = PresenceLedger[PresenceEntry]()
        self._subscribers: dict[uuid.UUID, dict[RealtimeConnection, str | None]] = {}
        self._viewer_subscriptions: Counter[str] = Counter()
        self._batches: set[asyncio.Task[None]] = set()

    async def subscribe(
        self, ws: RealtimeConnection, workspace_id: uuid.UUID, viewer_id: str | None
    ) -> bool:
        await ws.accept()
        if (
            viewer_id is not None
            and self._viewer_subscriptions[viewer_id] >= self._subscriptions_per_viewer
        ):
            return False
        # Registered before the snapshot goes out, so no change can fall between the two.
        self._subscribers.setdefault(workspace_id, {})[ws] = viewer_id
        if viewer_id is not None:
            self._viewer_subscriptions[viewer_id] += 1
        snapshot = WorkspacePresenceSnapshot(
            you=viewer_id,
            diagrams=[DiagramPresenceItem.of(item) for item in self._ledger.snapshot(workspace_id)],
        )
        await ws.send_text(snapshot.model_dump_json())
        return True

    def unsubscribe(self, ws: RealtimeConnection, workspace_id: uuid.UUID) -> None:
        subscribers = self._subscribers.get(workspace_id, {})
        if ws not in subscribers:
            return
        viewer_id = subscribers.pop(ws)
        if not subscribers:
            del self._subscribers[workspace_id]
        if viewer_id is None:
            return
        self._viewer_subscriptions[viewer_id] -= 1
        if self._viewer_subscriptions[viewer_id] == 0:
            del self._viewer_subscriptions[viewer_id]

    def room_changed(
        self, diagram_id: str, location: DiagramLocation, entries: list[PresenceEntry]
    ) -> None:
        watched = location.workspace_id in self._subscribers
        if not self._ledger.record(diagram_id, location, entries, watched):
            return
        batch = asyncio.create_task(self._send_batch_later(location.workspace_id))
        self._batches.add(batch)
        batch.add_done_callback(self._batch_done)

    async def _send_batch_later(self, workspace_id: uuid.UUID) -> None:
        await asyncio.sleep(self._batch_seconds)
        changes = self._ledger.take_changes(workspace_id)
        if not changes:
            return
        delta = WorkspacePresenceDelta(diagrams=[DiagramPresenceItem.of(item) for item in changes])
        await self._send(workspace_id, delta.model_dump_json())

    async def _send(self, workspace_id: uuid.UUID, message: str) -> None:
        subscribers = list(self._subscribers.get(workspace_id, {}))
        results = await asyncio.gather(
            *[ws.send_text(message) for ws in subscribers], return_exceptions=True
        )
        # A sidebar that can't be written to is gone; its own handler finishes closing it.
        for ws, result in zip(subscribers, results, strict=True):
            if isinstance(result, Exception):
                self.unsubscribe(ws, workspace_id)

    def _batch_done(self, batch: asyncio.Task[None]) -> None:
        self._batches.discard(batch)
        if batch.cancelled() or batch.exception() is None:
            return
        logger.error("workspace presence batch failed", exc_info=batch.exception())


workspace_presence_hub = WorkspacePresenceHub(
    WORKSPACE_PRESENCE_BATCH_SECONDS, WORKSPACE_PRESENCE_SUBSCRIPTIONS_PER_USER
)
