import asyncio
import logging
import uuid
from dataclasses import dataclass
from time import monotonic

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from app.common.settings import Settings, get_settings
from app.domain.constants.presence import (
    WORKSPACE_PRESENCE_MESSAGE_BURST,
    WORKSPACE_PRESENCE_MESSAGES_PER_SECOND,
    WORKSPACE_PRESENCE_RECHECK_SECONDS,
)
from app.domain.contracts.workspace_presence import WorkspacePresence
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import DomainError
from app.domain.services.token_bucket import TokenBucket
from app.domain.usecases.auth.authenticate_user import AuthenticateUserParams
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccessParams
from app.presentation.factories.presence_factories import (
    PresenceAccessScope,
    presence_access_factory,
    workspace_presence_factory,
)

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


# Who opened a sidebar on the workspace; user_id is None when authentication is disabled.
@dataclass(frozen=True)
class PresenceViewer:
    workspace_id: uuid.UUID
    user_id: uuid.UUID | None


async def is_member(
    user_id: uuid.UUID, workspace_id: uuid.UUID, access: PresenceAccessScope
) -> bool:
    try:
        async with access() as scope:
            await scope.authorize.execute(
                AuthorizeWorkspaceAccessParams(
                    user_id=user_id, required_role=WorkspaceRole.VIEWER, workspace_id=workspace_id
                )
            )
    except DomainError:
        return False
    return True


def parse_workspace_id(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


async def signed_in_user(token: str, access: PresenceAccessScope) -> uuid.UUID | None:
    if not token:
        return None
    try:
        async with access() as scope:
            user = await scope.authenticate.execute(AuthenticateUserParams(token=token))
    except DomainError:
        return None
    return user.id


# Only signed-in members see where the workspace's people are: guests on a share link have no
# token, and a valid token of someone outside the workspace is refused like a bad one.
async def admit_viewer(
    token: str, workspace_id: str, settings: Settings, access: PresenceAccessScope
) -> PresenceViewer | None:
    workspace = parse_workspace_id(workspace_id)
    if workspace is None:
        return None
    if not settings.auth_enabled:
        return PresenceViewer(workspace_id=workspace, user_id=None)
    user_id = await signed_in_user(token, access)
    if user_id is None or not await is_member(user_id, workspace, access):
        return None
    return PresenceViewer(workspace_id=workspace, user_id=user_id)


@router.websocket("/ws/workspaces/{workspace_id}/presence")
async def workspace_presence_websocket(
    ws: WebSocket,
    workspace_id: str,
    token: str = Query(default=""),
    settings: Settings = Depends(get_settings),
    access: PresenceAccessScope = Depends(presence_access_factory),
    presence: WorkspacePresence = Depends(workspace_presence_factory),
) -> None:
    viewer = await admit_viewer(token, workspace_id, settings, access)
    if viewer is None:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    viewer_id = str(viewer.user_id) if viewer.user_id is not None else None
    try:
        if not await presence.subscribe(ws, viewer.workspace_id, viewer_id):
            logger.info("refused an extra presence subscription to workspace %s", workspace_id)
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await watch_subscription(ws, viewer, access)
    except WebSocketDisconnect:
        pass
    finally:
        presence.unsubscribe(ws, viewer.workspace_id)


# Holds the subscription open until the client leaves, it floods a channel it has nothing to say
# on, or it loses access to the workspace. A failed membership check ends it too (fail closed).
async def watch_subscription(
    ws: WebSocket, viewer: PresenceViewer, access: PresenceAccessScope
) -> None:
    watchers = [asyncio.create_task(drain_until_closed(ws))]
    if viewer.user_id is not None:
        watchers.append(
            asyncio.create_task(
                revoke_when_removed(ws, viewer.user_id, viewer.workspace_id, access)
            )
        )
    try:
        done, _ = await asyncio.wait(watchers, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for watcher in watchers:
            watcher.cancel()
    for watcher in done:
        watcher.result()


async def drain_until_closed(ws: WebSocket) -> None:
    budget = TokenBucket(
        WORKSPACE_PRESENCE_MESSAGE_BURST, WORKSPACE_PRESENCE_MESSAGES_PER_SECOND, monotonic()
    )
    while (await ws.receive())["type"] != "websocket.disconnect":
        if not budget.try_take(monotonic()):
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return


async def revoke_when_removed(
    ws: WebSocket, user_id: uuid.UUID, workspace_id: uuid.UUID, access: PresenceAccessScope
) -> None:
    while True:
        await asyncio.sleep(WORKSPACE_PRESENCE_RECHECK_SECONDS)
        if not await is_member(user_id, workspace_id, access):
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
