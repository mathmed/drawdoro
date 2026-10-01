import uuid

import pytest

from app.domain.entities.models.comment import Comment
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.services.comment_ownership import is_created_by

ANA = uuid.uuid4()
BRUNO = uuid.uuid4()
ANAS_KEY = uuid.uuid4()
ANAS_OTHER_KEY = uuid.uuid4()
DIAGRAM = uuid.uuid4()

ANA_PERSON = CommentActor(user_id=ANA)
ANAS_AGENT = CommentActor(user_id=ANA, origin=RevisionOrigin.AGENT, api_key_id=ANAS_KEY)
OWNERLESS_AGENT = CommentActor(origin=RevisionOrigin.AGENT)


def by_person(author_id: uuid.UUID | None) -> Comment:
    return Comment(diagram_id=DIAGRAM, content="Hi", author_id=author_id)


def by_agent(owner: uuid.UUID | None, key: uuid.UUID | None) -> Comment:
    return Comment(
        diagram_id=DIAGRAM,
        content="Hi",
        author_id=owner,
        origin=RevisionOrigin.AGENT,
        api_key_id=key,
    )


def test_should_own_the_comments_written_with_the_same_key() -> None:
    assert is_created_by(by_agent(ANA, ANAS_KEY), ANAS_AGENT)


@pytest.mark.parametrize(
    "comment",
    [
        by_person(ANA),
        by_agent(ANA, ANAS_OTHER_KEY),
        by_agent(BRUNO, uuid.uuid4()),
        by_agent(None, None),
    ],
    ids=["owner-person", "owner-other-key", "other-person-agent", "ownerless-agent"],
)
def test_should_not_let_an_agent_own_anything_else(comment: Comment) -> None:
    assert not is_created_by(comment, ANAS_AGENT)


def test_should_let_ownerless_agents_share_their_comments() -> None:
    assert is_created_by(by_agent(None, None), OWNERLESS_AGENT)


@pytest.mark.parametrize(
    "comment",
    [by_person(None), by_person(ANA), by_agent(ANA, ANAS_KEY)],
    ids=["anonymous-person", "person", "keyed-agent"],
)
def test_should_not_let_ownerless_agents_own_other_comments(comment: Comment) -> None:
    assert not is_created_by(comment, OWNERLESS_AGENT)


def test_should_own_what_a_person_wrote_themselves() -> None:
    assert is_created_by(by_person(ANA), ANA_PERSON)


@pytest.mark.parametrize(
    "comment",
    [by_person(BRUNO), by_person(None), by_agent(ANA, ANAS_KEY)],
    ids=["someone-else", "anonymous", "own-agent"],
)
def test_should_not_let_a_person_own_other_comments(comment: Comment) -> None:
    assert not is_created_by(comment, ANA_PERSON)


def test_should_not_let_anonymous_people_own_anonymous_comments() -> None:
    assert not is_created_by(by_person(None), CommentActor())
