import uuid

from fastapi import APIRouter, Depends

from app.domain.entities.models.user import User
from app.domain.usecases.comment.create_comment import CreateComment, CreateCommentParams
from app.domain.usecases.comment.delete_comment import DeleteComment, DeleteCommentParams
from app.domain.usecases.comment.list_comments import ListComments, ListCommentsParams
from app.presentation.factories.comment_factories import (
    create_comment_factory,
    delete_comment_factory,
    list_comments_factory,
)
from app.presentation.fastapi.dependencies.current_user import get_current_user
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.comment_schemas import (
    CommentResponse,
    CreateCommentRequest,
)

router = APIRouter(
    prefix="/diagrams/{diagram_id}/comments",
    tags=["comments"],
    dependencies=[Depends(require_workspace_access)],
)


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    diagram_id: uuid.UUID,
    use_case: ListComments = Depends(list_comments_factory),
) -> list[CommentResponse]:
    comments = await use_case.execute(ListCommentsParams(diagram_id=diagram_id))
    return [CommentResponse.model_validate(c) for c in comments]


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    diagram_id: uuid.UUID,
    body: CreateCommentRequest,
    use_case: CreateComment = Depends(create_comment_factory),
    user: User | None = Depends(get_current_user),
) -> CommentResponse:
    comment = await use_case.execute(
        CreateCommentParams(
            diagram_id=diagram_id,
            element_id=body.element_id,
            content=body.content,
            # The signed-in user is the author; the body value only matters without auth.
            author_id=user.id if user is not None else body.author_id,
        )
    )
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    diagram_id: uuid.UUID,
    comment_id: uuid.UUID,
    use_case: DeleteComment = Depends(delete_comment_factory),
) -> None:
    await use_case.execute(DeleteCommentParams(comment_id=comment_id))
