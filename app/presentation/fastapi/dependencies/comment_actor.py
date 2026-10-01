from fastapi import Depends

from app.domain.entities.models.comment_actor import CommentActor
from app.domain.entities.models.revision_author import RevisionAuthor
from app.presentation.fastapi.dependencies.current_user import Caller, get_caller
from app.presentation.fastapi.dependencies.revision_author import get_revision_author


# Same identity as the diagram history, plus the key, so an agent only owns what its key wrote.
def get_comment_actor(
    caller: Caller = Depends(get_caller),
    author: RevisionAuthor = Depends(get_revision_author),
) -> CommentActor:
    return CommentActor(
        user_id=author.user_id,
        origin=author.origin,
        agent_name=author.agent_name,
        agent_label=author.agent_label,
        api_key_id=caller.api_key.id if caller.api_key is not None else None,
    )
