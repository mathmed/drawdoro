import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.entities.models.documentation_page import DocumentationPage
from app.infra.database.models.documentation_page import DocumentationPageORM


class DocumentationPageRepositoryImpl(DocumentationPageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_diagram(self, diagram_id: uuid.UUID) -> DocumentationPage | None:
        result = await self._session.execute(
            select(DocumentationPageORM).where(DocumentationPageORM.diagram_id == diagram_id)
        )
        orm = result.scalar_one_or_none()
        return _to_domain(orm) if orm else None

    async def upsert(self, page: DocumentationPage) -> DocumentationPage:
        result = await self._session.execute(
            select(DocumentationPageORM).where(DocumentationPageORM.diagram_id == page.diagram_id)
        )
        orm = result.scalar_one_or_none()
        if orm:
            orm.content = page.content
        else:
            orm = DocumentationPageORM(
                id=page.id,
                diagram_id=page.diagram_id,
                content=page.content,
            )
            self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)


def _to_domain(orm: DocumentationPageORM) -> DocumentationPage:
    return DocumentationPage(
        id=orm.id,
        diagram_id=orm.diagram_id,
        content=orm.content,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
