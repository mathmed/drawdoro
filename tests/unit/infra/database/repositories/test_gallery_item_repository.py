import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.infra.database.models.gallery_item import GalleryItemORM
from app.infra.database.repositories.gallery_item_repository import GalleryItemRepositoryImpl

PNG = b"\x89PNG\r\n\x1a\n"
OWNER_ID = uuid.uuid4()


def _orm(**overrides: object) -> GalleryItemORM:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "id": uuid.uuid4(),
        "owner_id": OWNER_ID,
        "name": "Logo",
        "kind": "image",
        "content": None,
        "image_data": PNG,
        "image_mime_type": "image/png",
        "thumbnail": PNG,
        "tags": ["brand"],
        "description": "Logo",
        "width": 64.0,
        "height": 32.0,
        "size_bytes": 8,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return GalleryItemORM(**values)


def _result(value: object) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    result.scalar_one.return_value = value
    result.scalars.return_value.all.return_value = value
    return result


@pytest.fixture
def session() -> MagicMock:
    mock = MagicMock(spec=AsyncSession)
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def sut(session: MagicMock) -> GalleryItemRepositoryImpl:
    return GalleryItemRepositoryImpl(session)


async def test_should_persist_new_item(sut: GalleryItemRepositoryImpl, session: MagicMock) -> None:
    item = GalleryItem(
        owner_id=OWNER_ID,
        name="Logo",
        kind=GalleryItemKind.IMAGE,
        image_data=PNG,
        image_mime_type=ImageMimeType.PNG,
        tags=["brand"],
        description="Logo",
        width=64,
        height=32,
        size_bytes=8,
    )

    async def fill_server_defaults(orm: GalleryItemORM) -> None:
        orm.created_at = orm.updated_at = datetime.now(UTC)

    session.refresh.side_effect = fill_server_defaults

    created = await sut.create(item)

    stored: GalleryItemORM = session.add.call_args.args[0]
    assert stored.kind == "image"
    assert stored.image_mime_type == "image/png"
    assert (stored.tags, stored.description) == (["brand"], "Logo")
    assert (stored.width, stored.height, stored.size_bytes) == (64, 32, 8)
    assert created.id == item.id
    assert created.image_data == PNG
    session.commit.assert_awaited_once()


async def test_should_map_stored_row_to_domain(
    sut: GalleryItemRepositoryImpl, session: MagicMock
) -> None:
    orm = _orm(kind="shapes", content={"shapes": [{}]}, image_data=None, image_mime_type=None)
    session.execute.return_value = _result(orm)

    item = await sut.get_by_id(orm.id)

    assert item is not None
    assert item.kind == GalleryItemKind.SHAPES
    assert item.content == {"shapes": [{}]}
    assert item.image_mime_type is None


async def test_should_return_none_when_missing(
    sut: GalleryItemRepositoryImpl, session: MagicMock
) -> None:
    session.execute.return_value = _result(None)
    assert await sut.get_by_id(uuid.uuid4()) is None


@pytest.mark.parametrize("owner_id", [OWNER_ID, None])
async def test_should_list_summaries_of_owner(
    sut: GalleryItemRepositoryImpl, session: MagicMock, owner_id: uuid.UUID | None
) -> None:
    session.execute.return_value = _result([_orm(owner_id=owner_id)])

    items = await sut.list_by_owner(owner_id)

    assert [item.name for item in items] == ["Logo"]
    assert not hasattr(items[0], "image_data")
    query = str(session.execute.await_args.args[0])
    assert "owner_id IS NULL" in query if owner_id is None else "owner_id =" in query


async def test_should_list_without_thumbnails_when_asked(
    sut: GalleryItemRepositoryImpl, session: MagicMock
) -> None:
    session.execute.return_value = _result([_orm()])

    items = await sut.list_by_owner(OWNER_ID, include_thumbnails=False)

    assert items[0].thumbnail is None
    assert items[0].tags == ["brand"]
    assert (items[0].width, items[0].height, items[0].size_bytes) == (64, 32, 8)


async def test_should_list_with_thumbnails_by_default(
    sut: GalleryItemRepositoryImpl, session: MagicMock
) -> None:
    session.execute.return_value = _result([_orm()])

    items = await sut.list_by_owner(OWNER_ID)

    assert items[0].thumbnail == PNG


async def test_should_update_name_tags_and_description(
    sut: GalleryItemRepositoryImpl, session: MagicMock
) -> None:
    orm = _orm()
    session.execute.return_value = _result(orm)
    summary = GalleryItemSummary(
        id=orm.id, name="New name", kind=GalleryItemKind.IMAGE, tags=["a", "b"], description=None
    )

    updated = await sut.update_details(summary)

    assert (orm.name, orm.tags, orm.description) == ("New name", ["a", "b"], None)
    assert (updated.name, updated.tags, updated.description) == ("New name", ["a", "b"], None)
    session.commit.assert_awaited_once()


async def test_should_map_rows_without_tags(
    sut: GalleryItemRepositoryImpl, session: MagicMock
) -> None:
    session.execute.return_value = _result(_orm(tags=None))

    item = await sut.get_by_id(uuid.uuid4())

    assert item is not None and item.tags == []


async def test_should_delete_item(sut: GalleryItemRepositoryImpl, session: MagicMock) -> None:
    orm = _orm()
    session.execute.return_value = _result(orm)

    await sut.delete(orm.id)

    session.delete.assert_awaited_once_with(orm)
    session.commit.assert_awaited_once()
