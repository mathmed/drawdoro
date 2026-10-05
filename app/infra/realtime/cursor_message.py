from typing import Literal

from pydantic import BaseModel

from app.domain.entities.objects.cursor_position import CanvasPoint


# What peers receive: the sender's presence id and name, as stamped by the server.
class CursorMessage(BaseModel):
    type: Literal["cursor"] = "cursor"
    id: str
    name: str
    point: CanvasPoint | None
    page: str | None
