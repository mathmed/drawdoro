from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.settings import Settings, get_settings
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.usecases.gallery.create_gallery_item import CreateGalleryItem
from app.domain.usecases.gallery.delete_gallery_item import DeleteGalleryItem
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem
from app.domain.usecases.gallery.list_gallery_items import ListGalleryItems
from app.domain.usecases.gallery.rename_gallery_item import RenameGalleryItem
from app.infra.database.repositories.gallery_item_repository import GalleryItemRepositoryImpl
from app.infra.database.session import get_session


async def create_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> CreateGalleryItem:
    limits = GalleryLimits(
        max_image_bytes=settings.gallery_max_image_bytes,
        max_shapes_bytes=settings.gallery_max_shapes_bytes,
    )
    return CreateGalleryItem(GalleryItemRepositoryImpl(session), limits)


async def list_gallery_items_factory(
    session: AsyncSession = Depends(get_session),
) -> ListGalleryItems:
    return ListGalleryItems(GalleryItemRepositoryImpl(session))


async def get_gallery_item_factory(session: AsyncSession = Depends(get_session)) -> GetGalleryItem:
    return GetGalleryItem(GalleryItemRepositoryImpl(session))


async def rename_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
) -> RenameGalleryItem:
    return RenameGalleryItem(GalleryItemRepositoryImpl(session))


async def delete_gallery_item_factory(
    session: AsyncSession = Depends(get_session),
) -> DeleteGalleryItem:
    return DeleteGalleryItem(GalleryItemRepositoryImpl(session))
