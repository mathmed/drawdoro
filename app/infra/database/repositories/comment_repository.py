import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domain.contracts.comment_repository import CommentRepository
from app.domain.entities.models.comment import Comment
from app.domain.enums.comment_status import CommentStatus
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import NotFoundError
from app.infra.database.models.comment import CommentORM
from app.infra.database.models.user import UserORM

Author = aliased(UserORM, name="author")
Resolver = aliased(UserORM, name="resolver")


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
            origin=comment.origin,
            agent_name=comment.agent_name,
            agent_label=comment.agent_label,
            api_key_id=comment.api_key_id,
        )
        self._session.add(orm)
        await self._session.commit()
        return await self._reload(comment.diagram_id, comment.id)

    async def list_by_diagram(
        self, diagram_id: uuid.UUID, status: CommentStatus = CommentStatus.ALL
    ) -> list[Comment]:
        query = _with_names().where(CommentORM.diagram_id == diagram_id)
        if status == CommentStatus.OPEN:
            query = query.where(CommentORM.resolved_at.is_(None))
        if status == CommentStatus.RESOLVED:
            query = query.where(CommentORM.resolved_at.is_not(None))
        result = await self._session.execute(query.order_by(CommentORM.created_at))
        return [_to_domain(orm, author, resolver) for orm, author, resolver in result.all()]

    async def get(self, diagram_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
        result = await self._session.execute(
            _with_names().where(CommentORM.id == comment_id, CommentORM.diagram_id == diagram_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        orm, author_name, resolver_name = row
        return _to_domain(orm, author_name, resolver_name)

    async def update_resolution(self, comment: Comment) -> Comment:
        orm = await self._session.get(CommentORM, comment.id)
        if orm is None:
            raise NotFoundError(f"Comment {comment.id} not found")
        orm.resolved_at = comment.resolved_at
        orm.resolved_by_id = comment.resolved_by_id
        orm.resolved_by_origin = comment.resolved_by_origin
        orm.resolved_by_agent_name = comment.resolved_by_agent_name
        orm.resolved_by_agent_label = comment.resolved_by_agent_label
        await self._session.commit()
        return await self._reload(comment.diagram_id, comment.id)

    async def delete(self, comment_id: uuid.UUID) -> None:
        orm = await self._session.get(CommentORM, comment_id)
        if orm is None:
            return
        await self._session.delete(orm)
        await self._session.commit()

    async def _reload(self, diagram_id: uuid.UUID, comment_id: uuid.UUID) -> Comment:
        comment = await self.get(diagram_id, comment_id)
        if comment is None:
            raise NotFoundError(f"Comment {comment_id} not found")
        return comment


def _with_names() -> Select[CommentORM, str, str]:
    return (
        select(CommentORM, Author.name, Resolver.name)
        .outerjoin(Author, Author.id == CommentORM.author_id)
        .outerjoin(Resolver, Resolver.id == CommentORM.resolved_by_id)
    )


def _to_domain(orm: CommentORM, author_name: str | None, resolver_name: str | None) -> Comment:
    return Comment(
        id=orm.id,
        diagram_id=orm.diagram_id,
        element_id=orm.element_id,
        content=orm.content,
        author_id=orm.author_id,
        author_name=author_name,
        origin=RevisionOrigin(orm.origin),
        agent_name=orm.agent_name,
        agent_label=orm.agent_label,
        api_key_id=orm.api_key_id,
        created_at=orm.created_at,
        resolved_at=orm.resolved_at,
        resolved_by_id=orm.resolved_by_id,
        resolved_by_name=resolver_name,
        resolved_by_origin=(
            RevisionOrigin(orm.resolved_by_origin) if orm.resolved_by_origin else None
        ),
        resolved_by_agent_name=orm.resolved_by_agent_name,
        resolved_by_agent_label=orm.resolved_by_agent_label,
    )
