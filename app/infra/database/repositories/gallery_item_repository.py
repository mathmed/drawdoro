import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.infra.database.models.gallery_item import GalleryItemORM

# The payloads can be megabytes each; summaries only need names, tags and thumbnails.
_SUMMARY_ONLY = (defer(GalleryItemORM.content), defer(GalleryItemORM.image_data))


class GalleryItemRepositoryImpl(GalleryItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, item: GalleryItem) -> GalleryItem:
        orm = GalleryItemORM(
            id=item.id,
            owner_id=item.owner_id,
            name=item.name,
            kind=item.kind.value,
            tags=item.tags,
            description=item.description,
            content=item.content,
            image_data=item.image_data,
            image_mime_type=item.image_mime_type.value if item.image_mime_type else None,
            thumbnail=item.thumbnail,
            width=item.width,
            height=item.height,
            size_bytes=item.size_bytes,
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

    async def list_by_owner(
        self, owner_id: uuid.UUID | None, include_thumbnails: bool = True
    ) -> list[GalleryItemSummary]:
        owner_filter = (
            GalleryItemORM.owner_id.is_(None)
            if owner_id is None
            else GalleryItemORM.owner_id == owner_id
        )
        options = (
            _SUMMARY_ONLY
            if include_thumbnails
            else (*_SUMMARY_ONLY, defer(GalleryItemORM.thumbnail))
        )
        result = await self._session.execute(
            select(GalleryItemORM)
            .options(*options)
            .where(owner_filter)
            .order_by(GalleryItemORM.created_at.desc())
        )
        return [_to_summary(row, include_thumbnails) for row in result.scalars().all()]

    async def update_details(self, item: GalleryItemSummary) -> GalleryItemSummary:
        result = await self._session.execute(
            select(GalleryItemORM).options(*_SUMMARY_ONLY).where(GalleryItemORM.id == item.id)
        )
        orm = result.scalar_one()
        orm.name = item.name
        orm.tags = list(item.tags)
        orm.description = item.description
        await self._session.commit()
        await self._session.refresh(
            orm, attribute_names=["name", "tags", "description", "updated_at"]
        )
        return _to_summary(orm)

    async def delete(self, item_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(GalleryItemORM).where(GalleryItemORM.id == item_id)
        )
        orm = result.scalar_one()
        await self._session.delete(orm)
        await self._session.commit()


def _to_summary(orm: GalleryItemORM, include_thumbnail: bool = True) -> GalleryItemSummary:
    return GalleryItemSummary(
        id=orm.id,
        owner_id=orm.owner_id,
        name=orm.name,
        kind=GalleryItemKind(orm.kind),
        tags=list(orm.tags or []),
        description=orm.description,
        image_mime_type=ImageMimeType(orm.image_mime_type) if orm.image_mime_type else None,
        thumbnail=orm.thumbnail if include_thumbnail else None,
        width=orm.width,
        height=orm.height,
        size_bytes=orm.size_bytes,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def _to_domain(orm: GalleryItemORM) -> GalleryItem:
    return GalleryItem(
        **_to_summary(orm).model_dump(), content=orm.content, image_data=orm.image_data
    )
