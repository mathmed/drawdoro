from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.comment.create_comment import CreateComment
from app.domain.usecases.comment.delete_comment import DeleteComment
from app.domain.usecases.comment.list_comments import ListComments
from app.domain.usecases.comment.update_comment_resolution import UpdateCommentResolution
from app.infra.database.repositories.comment_repository import CommentRepositoryImpl
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.session import get_session
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_comment_change_notifier import RealtimeCommentChangeNotifier


async def create_comment_factory(session: AsyncSession = Depends(get_session)) -> CreateComment:
    return CreateComment(
        CommentRepositoryImpl(session),
        DiagramRepositoryImpl(session),
        RealtimeCommentChangeNotifier(manager),
    )


async def list_comments_factory(session: AsyncSession = Depends(get_session)) -> ListComments:
    return ListComments(CommentRepositoryImpl(session), DiagramRepositoryImpl(session))


async def delete_comment_factory(session: AsyncSession = Depends(get_session)) -> DeleteComment:
    return DeleteComment(CommentRepositoryImpl(session), RealtimeCommentChangeNotifier(manager))


async def update_comment_resolution_factory(
    session: AsyncSession = Depends(get_session),
) -> UpdateCommentResolution:
    return UpdateCommentResolution(
        CommentRepositoryImpl(session), RealtimeCommentChangeNotifier(manager)
    )
