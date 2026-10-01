import uuid

from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.revision_origin import RevisionOrigin

USER_ID = uuid.uuid4()
KEY_ID = uuid.uuid4()


def test_should_label_people_by_id_in_logs() -> None:
    assert CommentActor(user_id=USER_ID).audit_label == f"user {USER_ID}"
    assert CommentActor().audit_label == "anonymous user"


def test_should_label_agents_by_owner_and_key_in_logs() -> None:
    actor = CommentActor(user_id=USER_ID, origin=RevisionOrigin.AGENT, api_key_id=KEY_ID)
    assert actor.is_agent
    assert actor.audit_label == f"agent of user {USER_ID} (key {KEY_ID})"


def test_should_label_ownerless_agents_in_logs() -> None:
    assert CommentActor(origin=RevisionOrigin.AGENT).audit_label == "ownerless agent"
