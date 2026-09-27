import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, diagram_id: str) -> None:
        await ws.accept()
        self._rooms.setdefault(diagram_id, set()).add(ws)

    def disconnect(self, ws: WebSocket, diagram_id: str) -> None:
        room = self._rooms.get(diagram_id, set())
        room.discard(ws)
        if not room:
            self._rooms.pop(diagram_id, None)

    def peer_count(self, diagram_id: str) -> int:
        return len(self._rooms.get(diagram_id, set()))

    async def broadcast(self, message: str, diagram_id: str, exclude: WebSocket) -> None:
        peers = list(self._rooms.get(diagram_id, set()))
        await asyncio.gather(
            *[ws.send_text(message) for ws in peers if ws is not exclude],
            return_exceptions=True,
        )


manager = ConnectionManager()
