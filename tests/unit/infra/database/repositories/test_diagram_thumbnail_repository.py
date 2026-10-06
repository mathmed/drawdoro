import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.engine import Compiled
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import ClauseElement

from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.thumbnail_theme import ThumbnailTheme
from app.infra.database.repositories.diagram_thumbnail_repository import (
    DiagramThumbnailRepositoryImpl,
)

# The dialect the API runs on, so the SQL is checked as Postgres will receive it.
POSTGRES = create_async_engine("postgresql+asyncpg://").dialect
PNG = b"\x89PNG\r\n\x1a\n"
DIAGRAM_ID = uuid.uuid4()


class Row:
    def __init__(self, **values: Any) -> None:
        self._values = values

    def _asdict(self) -> dict[str, Any]:
        return self._values


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def sut(session: AsyncMock) -> DiagramThumbnailRepositoryImpl:
    return DiagramThumbnailRepositoryImpl(session)


def compiled(session: AsyncMock) -> Compiled:
    statement: ClauseElement = session.execute.await_args.args[0]
    return statement.compile(dialect=POSTGRES)


async def test_should_list_the_live_project_thumbnails_of_one_theme_in_one_query(
    sut: DiagramThumbnailRepositoryImpl, session: AsyncMock
) -> None:
    project_id = uuid.uuid4()
    version = datetime(2026, 10, 6, 12, 0)
    result = MagicMock()
    result.all.return_value = [
        Row(diagram_id=DIAGRAM_ID, version=version, image=PNG, mime_type="image/png")
    ]
    session.execute.return_value = result

    thumbnails = await sut.list_by_project(project_id, ThumbnailTheme.DARK)

    assert thumbnails == [
        DiagramThumbnail(
            diagram_id=DIAGRAM_ID,
            theme=ThumbnailTheme.DARK,
            version=version,
            image=PNG,
            mime_type=ImageMimeType.PNG,
        )
    ]
    session.execute.assert_awaited_once()
    statement = compiled(session)
    sql = str(statement)
    assert "JOIN diagrams ON diagrams.id = diagram_thumbnails.diagram_id" in sql
    assert "diagrams.deleted_at IS NULL" in sql
    assert "diagram_thumbnails.image IS NOT NULL" in sql
    assert set(statement.params.values()) == {project_id, ThumbnailTheme.DARK}


async def test_should_upsert_both_themes_keeping_the_newest_version(
    sut: DiagramThumbnailRepositoryImpl, session: AsyncMock
) -> None:
    version = datetime(2026, 10, 6, 12, 0)
    await sut.save(
        [
            DiagramThumbnail(
                diagram_id=DIAGRAM_ID,
                theme=ThumbnailTheme.LIGHT,
                version=version,
                image=PNG,
                mime_type=ImageMimeType.PNG,
            ),
            DiagramThumbnail(diagram_id=DIAGRAM_ID, theme=ThumbnailTheme.DARK, version=version),
        ]
    )

    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()
    statement = compiled(session)
    sql = str(statement)
    assert "ON CONFLICT (diagram_id, theme) DO UPDATE" in sql
    assert "WHERE diagram_thumbnails.version <= excluded.version" in sql
    assert "updated_at = now()" in sql
    params = statement.params
    assert params["theme_m0"] == ThumbnailTheme.LIGHT
    assert params["image_m0"] == PNG
    assert params["theme_m1"] == ThumbnailTheme.DARK
    assert params["image_m1"] is None
    assert params["version_m0"] == version


async def test_should_store_an_aware_version_as_its_utc_time(
    sut: DiagramThumbnailRepositoryImpl, session: AsyncMock
) -> None:
    brasilia = timezone(timedelta(hours=-3))
    await sut.save(
        [
            DiagramThumbnail(
                diagram_id=DIAGRAM_ID,
                theme=ThumbnailTheme.LIGHT,
                version=datetime(2026, 10, 6, 9, 0, tzinfo=brasilia),
            )
        ]
    )

    assert compiled(session).params["version_m0"] == datetime(2026, 10, 6, 12, 0)


async def test_should_store_a_naive_version_unchanged(
    sut: DiagramThumbnailRepositoryImpl, session: AsyncMock
) -> None:
    version = datetime(2026, 10, 6, 12, 0)
    await sut.save(
        [DiagramThumbnail(diagram_id=DIAGRAM_ID, theme=ThumbnailTheme.LIGHT, version=version)]
    )

    stored = compiled(session).params["version_m0"]
    assert stored == version
    assert stored.tzinfo is None


async def test_should_not_touch_the_database_when_there_is_nothing_to_save(
    sut: DiagramThumbnailRepositoryImpl, session: AsyncMock
) -> None:
    await sut.save([])

    session.execute.assert_not_awaited()
    session.commit.assert_not_awaited()
