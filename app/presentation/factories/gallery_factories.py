from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.settings import Settings, get_settings
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.usecases.gallery.create_gallery_item import CreateGalleryItem
from app.domain.usecases.gallery.delete_gallery_item import DeleteGalleryItem
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem
from app.domain.usecases.gallery.insert_gallery_item import InsertGalleryItem
from app.domain.usecases.gallery.list_gallery_items import ListGalleryItems
from app.domain.usecases.gallery.update_gallery_item import UpdateGalleryItem
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.repositories.gallery_item_repository import GalleryItemRepositoryImpl
from app.infra.database.session import get_session
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_diagram_update_notifier import RealtimeDiagramUpdateNotifier
from app.presentation.factories.revision_factories import build_revision_recorder


def _limits(settings: Settings) -> GalleryLimits:
    return GalleryLimits(
        max_image_bytes=settings.gallery_max_image_bytes,
        max_shapes_bytes=settings.gallery_max_shapes_bytes,
        max_canvas_bytes=settings.gallery_max_canvas_bytes,
    )


async def create_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> CreateGalleryItem:
    return CreateGalleryItem(GalleryItemRepositoryImpl(session), _limits(settings))


async def list_gallery_items_factory(
    session: AsyncSession = Depends(get_session),
) -> ListGalleryItems:
    return ListGalleryItems(GalleryItemRepositoryImpl(session))


async def get_gallery_item_factory(session: AsyncSession = Depends(get_session)) -> GetGalleryItem:
    return GetGalleryItem(GalleryItemRepositoryImpl(session))


async def update_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
) -> UpdateGalleryItem:
    return UpdateGalleryItem(GalleryItemRepositoryImpl(session))


async def delete_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
) -> DeleteGalleryItem:
    return DeleteGalleryItem(GalleryItemRepositoryImpl(session))


async def insert_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> InsertGalleryItem:
    return InsertGalleryItem(
        GalleryItemRepositoryImpl(session),
        DiagramRepositoryImpl(session),
        RealtimeDiagramUpdateNotifier(manager),
        build_revision_recorder(session),
        _limits(settings),
    )
