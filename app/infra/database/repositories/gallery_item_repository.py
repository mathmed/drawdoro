import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.infra.database.models.gallery_item import GalleryItemORM


class GalleryItemRepositoryImpl(GalleryItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: GalleryItem) -> GalleryItem:
        orm = GalleryItemORM(
            id=item.id,
            owner_id=item.owner_id,
            name=item.name,
            kind=item.kind.value,
            content=item.content,
            image_data=item.image_data,
            image_mime_type=item.image_mime_type.value if item.image_mime_type else None,
            thumbnail=item.thumbnail,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def get_by_id(self, item_id: uuid.UUID) -> GalleryItem | None:
        result = await self._session.execute(
            select(GalleryItemORM).where(GalleryItemORM.id == item_id)
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def list_by_owner(self, owner_id: uuid.UUID | None) -> list[GalleryItemSummary]:
        owner_filter = (
            GalleryItemORM.owner_id.is_(None)
            if owner_id is None
            else GalleryItemORM.owner_id == owner_id
        )
        # The payloads can be megabytes each; listing only needs names and thumbnails.
        result = await self._session.execute(
            select(GalleryItemORM)
            .options(defer(GalleryItemORM.content), defer(GalleryItemORM.image_data))
            .where(owner_filter)
            .order_by(GalleryItemORM.created_at.desc())
        )
        return [_to_summary(row) for row in result.scalars().all()]

    async def rename(self, item_id: uuid.UUID, name: str) -> GalleryItemSummary:
        result = await self._session.execute(
            select(GalleryItemORM)
            .options(defer(GalleryItemORM.content), defer(GalleryItemORM.image_data))
            .where(GalleryItemORM.id == item_id)
        )
        orm = result.scalar_one()
        orm.name = name
        await self._session.commit()
        await self._session.refresh(orm, attribute_names=["name", "updated_at"])
        return _to_summary(orm)

    async def delete(self, item_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(GalleryItemORM).where(GalleryItemORM.id == item_id)
        )
        orm = result.scalar_one()
        await self._session.delete(orm)
        await self._session.commit()


def _to_summary(orm: GalleryItemORM) -> GalleryItemSummary:
    return GalleryItemSummary(
        id=orm.id,
        owner_id=orm.owner_id,
        name=orm.name,
        kind=GalleryItemKind(orm.kind),
        image_mime_type=ImageMimeType(orm.image_mime_type) if orm.image_mime_type else None,
        thumbnail=orm.thumbnail,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def _to_domain(orm: GalleryItemORM) -> GalleryItem:
    return GalleryItem(
        **_to_summary(orm).model_dump(), content=orm.content, image_data=orm.image_data
    )
