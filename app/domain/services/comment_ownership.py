from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.revision_origin import RevisionOrigin


# An agent owns only the comments written with its own key: never a person's, nor another
# agent's, even one working for the same person. Ownerless agents (the shared service key) share
# one identity. A person owns what they wrote themselves, not what their agent wrote.
def is_created_by(comment: Comment, actor: CommentActor) -> bool:
    if actor.is_agent:
        return comment.origin == RevisionOrigin.AGENT and comment.api_key_id == actor.api_key_id
    return (
        comment.origin == RevisionOrigin.HUMAN
        and actor.user_id is not None
        and comment.author_id == actor.user_id
    )
