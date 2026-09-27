from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.comment.create_comment import CreateComment
from app.domain.usecases.comment.delete_comment import DeleteComment
from app.domain.usecases.comment.list_comments import ListComments
from app.infra.database.repositories.comment_repository import CommentRepositoryImpl
from app.infra.database.session import get_session


async def create_comment_factory(session: AsyncSession = Depends(get_session)) -> CreateComment:
    return CreateComment(CommentRepositoryImpl(session))


async def list_comments_factory(session: AsyncSession = Depends(get_session)) -> ListComments:
    return ListComments(CommentRepositoryImpl(session))


async def delete_comment_factory(session: AsyncSession = Depends(get_session)) -> DeleteComment:
    return DeleteComment(CommentRepositoryImpl(session))
