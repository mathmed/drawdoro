import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.contracts.comment_change_notifier import CommentChangeNotifier
from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.comment_actor import CommentActor
from app.domain.enums.revision_origin import RevisionOrigin

DIAGRAM_ID = uuid.uuid4()
ANA_ID = uuid.uuid4()
ANAS_KEY_ID = uuid.uuid4()
ANA = CommentActor(user_id=ANA_ID)
ANAS_AGENT = CommentActor(
    user_id=ANA_ID,
    origin=RevisionOrigin.AGENT,
    agent_name="Claude",
    agent_label="laptop",
    api_key_id=ANAS_KEY_ID,
)
OWNERLESS_AGENT = CommentActor(origin=RevisionOrigin.AGENT, agent_name="Claude")


@pytest.fixture
def comments() -> AsyncMock:
    repo = AsyncMock(spec=CommentRepository)
    repo.create.side_effect = lambda comment: comment
    repo.update_resolution.side_effect = lambda comment: comment
    return repo


@pytest.fixture
def diagrams() -> AsyncMock:
    repo = AsyncMock(spec=DiagramRepository)
    repo.exists.return_value = True
    return repo


@pytest.fixture
def notifier() -> AsyncMock:
    return AsyncMock(spec=CommentChangeNotifier)
