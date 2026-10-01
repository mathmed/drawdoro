import uuid

from fastapi import APIRouter, Depends, Query

from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.comment_status import CommentStatus
from app.domain.usecases.comment.create_comment import CreateComment, CreateCommentParams
from app.domain.usecases.comment.delete_comment import DeleteComment, DeleteCommentParams
from app.domain.usecases.comment.list_comments import ListComments, ListCommentsParams
from app.domain.usecases.comment.update_comment_resolution import (
    UpdateCommentResolution,
    UpdateCommentResolutionParams,
)
from app.presentation.factories.comment_factories import (
    create_comment_factory,
    delete_comment_factory,
    list_comments_factory,
    update_comment_resolution_factory,
)
from app.presentation.fastapi.dependencies.agent_presence import track_agent_activity
from app.presentation.fastapi.dependencies.comment_actor import get_comment_actor
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.comment_schemas import (
    CommentResponse,
    CreateCommentRequest,
    UpdateCommentRequest,
)

# Reads need any membership; creating, resolving and deleting need the editor role.
router = APIRouter(
    prefix="/diagrams/{diagram_id}/comments",
    tags=["comments"],
    dependencies=[Depends(require_workspace_access), Depends(track_agent_activity)],
)


@router.get("", response_model=list[CommentResponse])
async def list_comments(
    diagram_id: uuid.UUID,
    status: CommentStatus = Query(default=CommentStatus.ALL),
    actor: CommentActor = Depends(get_comment_actor),
    use_case: ListComments = Depends(list_comments_factory),
) -> list[CommentResponse]:
    comments = await use_case.execute(
        ListCommentsParams(diagram_id=diagram_id, status=status, actor=actor)
    )
    return [CommentResponse.model_validate(c) for c in comments]


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    diagram_id: uuid.UUID,
    body: CreateCommentRequest,
    actor: CommentActor = Depends(get_comment_actor),
    use_case: CreateComment = Depends(create_comment_factory),
) -> CommentResponse:
    comment = await use_case.execute(
        CreateCommentParams(
            diagram_id=diagram_id,
            element_id=body.element_id,
            content=body.content,
            actor=actor,
            author_id=body.author_id,
        )
    )
    return CommentResponse.model_validate(comment)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    diagram_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: UpdateCommentRequest,
    actor: CommentActor = Depends(get_comment_actor),
    use_case: UpdateCommentResolution = Depends(update_comment_resolution_factory),
) -> CommentResponse:
    comment = await use_case.execute(
        UpdateCommentResolutionParams(
            diagram_id=diagram_id, comment_id=comment_id, resolved=body.resolved, actor=actor
        )
    )
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    diagram_id: uuid.UUID,
    comment_id: uuid.UUID,
    actor: CommentActor = Depends(get_comment_actor),
    use_case: DeleteComment = Depends(delete_comment_factory),
) -> None:
    await use_case.execute(
        DeleteCommentParams(diagram_id=diagram_id, comment_id=comment_id, actor=actor)
    )
