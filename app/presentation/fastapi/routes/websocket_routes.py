import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.infra.realtime.connection_manager import manager

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/diagrams/{diagram_id}")
async def diagram_websocket(ws: WebSocket, diagram_id: str) -> None:
    await manager.connect(ws, diagram_id)
    logger.info(
        "cliente conectado ao diagrama %s — peers: %d",
        diagram_id,
        manager.peer_count(diagram_id),
    )

    # Notificar todos sobre nova conexao
    await manager.broadcast(
        json.dumps({"type": "peer_joined", "peers": manager.peer_count(diagram_id)}),
        diagram_id,
        exclude=ws,
    )
    # Enviar contagem atual para o recem-chegado
    await ws.send_text(json.dumps({"type": "peers", "peers": manager.peer_count(diagram_id)}))

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") in {"update", "cursor"}:
                # Broadcast do snapshot / cursor para os outros peers
                await manager.broadcast(data, diagram_id, exclude=ws)
    except WebSocketDisconnect:
        manager.disconnect(ws, diagram_id)
        logger.info(
            "cliente desconectado do diagrama %s — peers: %d",
            diagram_id,
            manager.peer_count(diagram_id),
        )
        await manager.broadcast(
            json.dumps({"type": "peer_left", "peers": manager.peer_count(diagram_id)}),
            diagram_id,
            exclude=ws,
        )
