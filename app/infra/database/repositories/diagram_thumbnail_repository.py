import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.diagram_thumbnail_repository import DiagramThumbnailRepository
from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.thumbnail_theme import ThumbnailTheme
from app.infra.database.models.diagram import DiagramORM
from app.infra.database.models.diagram_thumbnail import DiagramThumbnailORM


class DiagramThumbnailRepositoryImpl(DiagramThumbnailRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_project(
        self, project_id: uuid.UUID, theme: ThumbnailTheme
    ) -> list[DiagramThumbnail]:
        result = await self._session.execute(
            select(
                DiagramThumbnailORM.diagram_id,
                DiagramThumbnailORM.version,
                DiagramThumbnailORM.image,
                DiagramThumbnailORM.mime_type,
            )
            .join(DiagramORM, DiagramORM.id == DiagramThumbnailORM.diagram_id)
            .where(
                DiagramORM.project_id == project_id,
                DiagramORM.deleted_at.is_(None),
                DiagramThumbnailORM.theme == theme,
                DiagramThumbnailORM.image.is_not(None),
            )
        )
        return [DiagramThumbnail(theme=theme, **row._asdict()) for row in result.all()]

    async def save(self, thumbnails: list[DiagramThumbnail]) -> None:
        if not thumbnails:
            return
        statement = insert(DiagramThumbnailORM).values(
            [
                {
                    "diagram_id": thumbnail.diagram_id,
                    "theme": thumbnail.theme,
                    "version": _stored_version(thumbnail.version),
                    "image": thumbnail.image,
                    "mime_type": thumbnail.mime_type,
                }
                for thumbnail in thumbnails
            ]
        )
        # One statement: the version check and the write can't interleave with another upload.
        statement = statement.on_conflict_do_update(
            index_elements=[DiagramThumbnailORM.diagram_id, DiagramThumbnailORM.theme],
            set_={
                "version": statement.excluded.version,
                "image": statement.excluded.image,
                "mime_type": statement.excluded.mime_type,
                "updated_at": func.now(),
            },
            where=DiagramThumbnailORM.version <= statement.excluded.version,
        )
        await self._session.execute(statement)
        await self._session.commit()


# The column has no time zone, like diagrams.updated_at; an aware value is stored as its UTC time.
def _stored_version(version: datetime) -> datetime:
    if version.tzinfo is None:
        return version
    return version.astimezone(UTC).replace(tzinfo=None)
