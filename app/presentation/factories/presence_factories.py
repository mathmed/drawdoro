from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.diagram_rooms import DiagramRooms
from app.domain.contracts.workspace_presence import WorkspacePresence
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.presence.track_agent_activity import TrackAgentActivity
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.session import AsyncSessionLocal, get_session
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_agent_presence import RealtimeAgentPresence
from app.infra.realtime.workspace_presence_hub import workspace_presence_hub
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)


async def track_agent_activity_factory(
    session: AsyncSession = Depends(get_session),
) -> TrackAgentActivity:
    return TrackAgentActivity(DiagramRepositoryImpl(session), RealtimeAgentPresence(manager))


# One registry per process: every editor of a diagram must land in the same room.
def diagram_rooms_factory() -> DiagramRooms:
    return manager


def workspace_presence_factory() -> WorkspacePresence:
    return workspace_presence_hub


@dataclass(frozen=True)
class PresenceAccess:
    authenticate: AuthenticateUser
    authorize: AuthorizeWorkspaceAccess


type PresenceAccessScope = Callable[[], AbstractAsyncContextManager[PresenceAccess]]


# A sidebar subscription lives for hours: each check gets its own short session instead of holding
# a database connection for as long as the socket is open.
@asynccontextmanager
async def open_presence_access() -> AsyncIterator[PresenceAccess]:
    async with AsyncSessionLocal() as session:
        yield PresenceAccess(
            authenticate=await authenticate_user_factory(session),
            authorize=await authorize_workspace_access_factory(session),
        )


def presence_access_factory() -> PresenceAccessScope:
    return open_presence_access
