import uuid
from typing import Literal

from pydantic import BaseModel

from app.domain.contracts.comment_change_notifier import CommentChangeNotifier
from app.infra.realtime.connection_manager import ConnectionManager


# Carries no comment text: guests on a share link are in the same room and can't read comments.
class CommentsChangedMessage(BaseModel):
    type: Literal["comments_changed"] = "comments_changed"
    diagram_id: uuid.UUID


class RealtimeCommentChangeNotifier(CommentChangeNotifier):
    def __init__(self, connections: ConnectionManager) -> None:
        self._connections = connections

    async def notify_changed(self, diagram_id: uuid.UUID) -> None:
        message = CommentsChangedMessage(diagram_id=diagram_id)
        await self._connections.broadcast(message.model_dump_json(), str(diagram_id))
