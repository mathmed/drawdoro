from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.diagram.create_diagram import CreateDiagram
from app.domain.usecases.diagram.delete_diagram import DeleteDiagram
from app.domain.usecases.diagram.get_diagram import GetDiagram
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.get_diagram_location import GetDiagramLocation
from app.domain.usecases.diagram.list_diagram_thumbnails import ListDiagramThumbnails
from app.domain.usecases.diagram.list_diagrams import ListDiagrams
from app.domain.usecases.diagram.save_diagram_thumbnail import SaveDiagramThumbnail
from app.domain.usecases.diagram.share_diagram import ShareDiagram
from app.domain.usecases.diagram.update_diagram import UpdateDiagram
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.repositories.diagram_thumbnail_repository import (
    DiagramThumbnailRepositoryImpl,
)
from app.infra.database.session import get_session
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_diagram_update_notifier import RealtimeDiagramUpdateNotifier
from app.presentation.factories.revision_factories import build_revision_recorder


async def create_diagram_factory(session: AsyncSession = Depends(get_session)) -> CreateDiagram:
    return CreateDiagram(DiagramRepositoryImpl(session))


async def get_diagram_factory(session: AsyncSession = Depends(get_session)) -> GetDiagram:
    return GetDiagram(DiagramRepositoryImpl(session))


async def list_diagrams_factory(session: AsyncSession = Depends(get_session)) -> ListDiagrams:
    return ListDiagrams(DiagramRepositoryImpl(session))


async def list_diagram_thumbnails_factory(
    session: AsyncSession = Depends(get_session),
) -> ListDiagramThumbnails:
    return ListDiagramThumbnails(DiagramThumbnailRepositoryImpl(session))


async def save_diagram_thumbnail_factory(
    session: AsyncSession = Depends(get_session),
) -> SaveDiagramThumbnail:
    return SaveDiagramThumbnail(
        DiagramRepositoryImpl(session), DiagramThumbnailRepositoryImpl(session)
    )


async def update_diagram_factory(session: AsyncSession = Depends(get_session)) -> UpdateDiagram:
    return UpdateDiagram(
        DiagramRepositoryImpl(session),
        RealtimeDiagramUpdateNotifier(manager),
        build_revision_recorder(session),
    )


async def delete_diagram_factory(session: AsyncSession = Depends(get_session)) -> DeleteDiagram:
    return DeleteDiagram(DiagramRepositoryImpl(session))


async def share_diagram_factory(session: AsyncSession = Depends(get_session)) -> ShareDiagram:
    return ShareDiagram(DiagramRepositoryImpl(session))


async def get_diagram_by_share_token_factory(
    session: AsyncSession = Depends(get_session),
) -> GetDiagramByShareToken:
    return GetDiagramByShareToken(DiagramRepositoryImpl(session))


async def get_diagram_location_factory(
    session: AsyncSession = Depends(get_session),
) -> GetDiagramLocation:
    return GetDiagramLocation(DiagramRepositoryImpl(session))
