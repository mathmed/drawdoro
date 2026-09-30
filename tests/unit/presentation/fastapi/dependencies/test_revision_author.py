from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.models.user import User
from app.domain.enums.revision_origin import RevisionOrigin
from app.presentation.fastapi.dependencies.current_user import Caller
from app.presentation.fastapi.dependencies.revision_author import get_revision_author

ANA = User(email="ana@example.com", name="Ana", picture_url="https://example.com/ana.png")
ANAS_KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_abc", key_hash="hash")
CLAUDE = AgentIdentity(id="agent:Claude", name="Claude")


def test_should_attribute_editor_saves_to_the_person() -> None:
    assert get_revision_author(caller=Caller(user=ANA), agent=None) == RevisionAuthor(
        user_id=ANA.id, name="Ana", picture_url="https://example.com/ana.png"
    )


def test_should_attribute_personal_key_changes_to_the_owners_agent() -> None:
    author = get_revision_author(caller=Caller(user=ANA, api_key=ANAS_KEY), agent=CLAUDE)
    assert author.origin == RevisionOrigin.AGENT
    assert (author.user_id, author.name) == (ANA.id, "Ana")
    assert (author.agent_name, author.agent_label) == ("Claude", "laptop")


def test_should_attribute_service_key_changes_to_an_ownerless_agent() -> None:
    author = get_revision_author(caller=Caller(is_service=True), agent=None)
    assert author == RevisionAuthor(origin=RevisionOrigin.AGENT)


def test_should_attribute_unnamed_requests_without_auth_to_a_person() -> None:
    assert get_revision_author(caller=Caller(), agent=None) == RevisionAuthor()
