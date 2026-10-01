from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.models.user import User
from app.domain.enums.revision_origin import RevisionOrigin
from app.presentation.fastapi.dependencies.comment_actor import get_comment_actor
from app.presentation.fastapi.dependencies.current_user import Caller

ANA = User(email="ana@example.com", name="Ana")
ANAS_KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_abc", key_hash="hash")


def test_should_act_as_the_owners_agent_with_its_key() -> None:
    author = RevisionAuthor(
        user_id=ANA.id,
        name="Ana",
        origin=RevisionOrigin.AGENT,
        agent_name="Claude",
        agent_label="laptop",
    )
    actor = get_comment_actor(caller=Caller(user=ANA, api_key=ANAS_KEY), author=author)
    assert actor == CommentActor(
        user_id=ANA.id,
        origin=RevisionOrigin.AGENT,
        agent_name="Claude",
        agent_label="laptop",
        api_key_id=ANAS_KEY.id,
    )


def test_should_act_as_an_ownerless_agent_with_the_service_key() -> None:
    author = RevisionAuthor(origin=RevisionOrigin.AGENT, agent_name="Claude")
    actor = get_comment_actor(caller=Caller(is_service=True), author=author)
    assert actor == CommentActor(origin=RevisionOrigin.AGENT, agent_name="Claude")


def test_should_act_as_the_signed_in_person() -> None:
    author = RevisionAuthor(user_id=ANA.id, name="Ana")
    assert get_comment_actor(caller=Caller(user=ANA), author=author) == CommentActor(user_id=ANA.id)
