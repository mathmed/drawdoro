from fastapi import Depends

from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.models.user import User
from app.domain.enums.revision_origin import RevisionOrigin
from app.presentation.fastapi.dependencies.agent_presence import get_agent_identity
from app.presentation.fastapi.dependencies.current_user import Caller, get_caller


# Changes made with a personal key are the owner's agent's; the service key is an ownerless agent.
def get_revision_author(
    caller: Caller = Depends(get_caller),
    agent: AgentIdentity | None = Depends(get_agent_identity),
) -> RevisionAuthor:
    person = _person(caller.user)
    label = caller.api_key.label if caller.api_key is not None else None
    if agent is None and caller.api_key is None and not caller.is_service:
        return person
    return _as_agent(person, agent, label)


def _person(user: User | None) -> RevisionAuthor:
    if user is None:
        return RevisionAuthor()
    return RevisionAuthor(user_id=user.id, name=user.name, picture_url=user.picture_url)


def _as_agent(
    person: RevisionAuthor, agent: AgentIdentity | None, label: str | None
) -> RevisionAuthor:
    return person.model_copy(
        update={
            "origin": RevisionOrigin.AGENT,
            "agent_name": agent.name if agent is not None else None,
            "agent_label": label,
        }
    )
