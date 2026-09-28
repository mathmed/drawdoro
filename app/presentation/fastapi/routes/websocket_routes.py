import json
import logging
import uuid

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from app.common.settings import Settings, get_settings
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import DomainError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser, AuthenticateUserParams
from app.domain.usecases.auth.authorize_workspace_access import (
    AuthorizeWorkspaceAccess,
    AuthorizeWorkspaceAccessParams,
)
from app.infra.realtime.connection_manager import Participant, manager
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


async def resolve_participant(
    token: str,
    diagram_id: str,
    settings: Settings,
    authenticate: AuthenticateUser,
    authorize: AuthorizeWorkspaceAccess,
) -> Participant | None:
    # Browsers can't set headers on a WebSocket handshake, so the ID token travels in the URL.
    if not settings.auth_enabled:
        return Participant(name="Guest")
    try:
        user = await authenticate.execute(AuthenticateUserParams(token=token))
        await authorize.execute(
            AuthorizeWorkspaceAccessParams(
                user_id=user.id,
                required_role=WorkspaceRole.VIEWER,
                diagram_id=uuid.UUID(diagram_id),
            )
        )
    except DomainError, ValueError:
        return None
    return Participant(name=user.name, user_id=str(user.id))


@router.websocket("/ws/diagrams/{diagram_id}")
async def diagram_websocket(
    ws: WebSocket,
    diagram_id: str,
    token: str = Query(default=""),
    settings: Settings = Depends(get_settings),
    authenticate: AuthenticateUser = Depends(authenticate_user_factory),
    authorize: AuthorizeWorkspaceAccess = Depends(authorize_workspace_access_factory),
) -> None:
    participant = await resolve_participant(token, diagram_id, settings, authenticate, authorize)
    if participant is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(ws, diagram_id, participant)
    logger.info(
        "participant joined diagram %s (%d online)", diagram_id, manager.peer_count(diagram_id)
    )
    try:
        await manager.broadcast_presence(diagram_id)
        await relay_updates(ws, diagram_id)
    except WebSocketDisconnect:
        pass
    finally:
        # Any exit (clean close, dropped network, bad message) must free the seat.
        manager.disconnect(ws, diagram_id)
        logger.info(
            "participant left diagram %s (%d online)", diagram_id, manager.peer_count(diagram_id)
        )
        await manager.broadcast_presence(diagram_id)


async def relay_updates(ws: WebSocket, diagram_id: str) -> None:
    while True:
        data = await ws.receive_text()
        try:
            kind = json.loads(data).get("type")
        except ValueError, AttributeError:
            # A malformed message is dropped instead of taking the whole session down.
            continue
        if kind in {"update", "cursor"}:
            await manager.broadcast(data, diagram_id, exclude=ws)
