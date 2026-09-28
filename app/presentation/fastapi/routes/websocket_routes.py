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
from app.domain.usecases.diagram.get_diagram_by_share_token import (
    GetDiagramByShareToken,
    GetDiagramByShareTokenParams,
)
from app.infra.realtime.connection_manager import Participant, manager
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.diagram_factories import get_diagram_by_share_token_factory

GUEST_NAME_MAX_LENGTH = 40

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


async def resolve_guest(
    share: str,
    guest_name: str,
    diagram_id: str,
    shared_lookup: GetDiagramByShareToken,
) -> Participant | None:
    # Guests reach a diagram only through a valid share link, and always as read-only viewers.
    if share == "":
        return None
    try:
        diagram = await shared_lookup.execute(GetDiagramByShareTokenParams(share_token=share))
    except DomainError:
        return None
    if str(diagram.id) != diagram_id:
        return None
    name = guest_name.strip()[:GUEST_NAME_MAX_LENGTH] or "Guest"
    return Participant(name=name)


async def resolve_participant(
    token: str,
    share: str,
    guest_name: str,
    diagram_id: str,
    settings: Settings,
    authenticate: AuthenticateUser,
    authorize: AuthorizeWorkspaceAccess,
    shared_lookup: GetDiagramByShareToken,
) -> Participant | None:
    # Browsers can't set headers on a WebSocket handshake, so the ID token travels in the URL.
    if not settings.auth_enabled:
        return Participant(name="Guest")
    if token == "":
        return await resolve_guest(share, guest_name, diagram_id, shared_lookup)
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
    share: str = Query(default=""),
    guest_name: str = Query(default="", alias="name"),
    settings: Settings = Depends(get_settings),
    authenticate: AuthenticateUser = Depends(authenticate_user_factory),
    authorize: AuthorizeWorkspaceAccess = Depends(authorize_workspace_access_factory),
    shared_lookup: GetDiagramByShareToken = Depends(get_diagram_by_share_token_factory),
) -> None:
    participant = await resolve_participant(
        token, share, guest_name, diagram_id, settings, authenticate, authorize, shared_lookup
    )
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
