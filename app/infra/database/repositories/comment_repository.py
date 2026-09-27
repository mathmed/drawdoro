import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.comment_repository import CommentRepository
from app.domain.entities.models.comment import Comment
from app.infra.database.models.comment import CommentORM


class CommentRepositoryImpl(CommentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, comment: Comment) -> Comment:
        orm = CommentORM(
            id=comment.id,
            diagram_id=comment.diagram_id,
            element_id=comment.element_id,
            content=comment.content,
            author_id=comment.author_id,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _to_domain(orm)

    async def list_by_diagram(self, diagram_id: uuid.UUID) -> list[Comment]:
        result = await self._session.execute(
            select(CommentORM).where(CommentORM.diagram_id == diagram_id)
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def delete(self, comment_id: uuid.UUID) -> None:
        result = await self._session.execute(select(CommentORM).where(CommentORM.id == comment_id))
        orm = result.scalar_one()
        await self._session.delete(orm)
        await self._session.commit()


def _to_domain(orm: CommentORM) -> Comment:
    return Comment(
        id=orm.id,
        diagram_id=orm.diagram_id,
        element_id=orm.element_id,
        content=orm.content,
        author_id=orm.author_id,
        created_at=orm.created_at,
    )
