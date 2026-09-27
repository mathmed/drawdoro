from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/diagrams/{diagram_id}")
async def diagram_websocket(websocket: WebSocket, diagram_id: str) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "diagram_id": diagram_id})
    await websocket.close(code=1001, reason="real-time not yet implemented")
