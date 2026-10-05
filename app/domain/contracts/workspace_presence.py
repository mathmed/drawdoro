import uuid
from abc import ABC, abstractmethod

from app.domain.contracts.realtime_connection import RealtimeConnection


# Who is in each diagram of a workspace, for its members' sidebars: one connection per open
# sidebar instead of one per diagram. Callers admit only members of the workspace.
class WorkspacePresence(ABC):
    # Sends the current presence and then every change. False when the viewer already has as many
    # subscriptions as allowed; viewer_id is None when authentication is disabled.
    @abstractmethod
    async def subscribe(
        self, ws: RealtimeConnection, workspace_id: uuid.UUID, viewer_id: str | None
    ) -> bool: ...

    @abstractmethod
    def unsubscribe(self, ws: RealtimeConnection, workspace_id: uuid.UUID) -> None: ...
