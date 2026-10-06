import uuid
from collections.abc import Callable, Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.user import User
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import ForbiddenError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.presence.track_agent_activity import TrackAgentActivity
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.presence_factories import track_agent_activity_factory
from app.presentation.factories.revision_factories import (
    get_diagram_revision_factory,
    list_diagram_revisions_factory,
    restore_diagram_revision_factory,
)

ANA = User(email="ana@example.com", name="Ana")
DIAGRAM = Diagram(project_id=uuid.uuid4(), name="Checkout", canvas_state={"shapes": ["old"]})
REVISION = DiagramRevision(
    diagram_id=DIAGRAM.id,
    origin=RevisionOrigin.AGENT,
    author_id=ANA.id,
    author_name="Ana",
    agent_name="Claude",
    agent_label="laptop",
    summary="Added a queue",
    snapshot=DiagramSnapshot(name="Checkout", canvas_state={"shapes": ["old"]}),
)
BASE = f"/diagrams/{DIAGRAM.id}/revisions"


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def override(factory: Callable[..., object], result: object) -> AsyncMock:
    mock = AsyncMock()
    mock.execute.return_value = result
    app.dependency_overrides[factory] = lambda: mock
    return mock


def test_should_list_revisions_without_snapshots(client: TestClient) -> None:
    listed = REVISION.model_copy(update={"snapshot": None})
    mock = override(list_diagram_revisions_factory, [listed])
    response = client.get(f"{BASE}?limit=5")
    assert response.status_code == 200
    [body] = response.json()
    assert body["agent_label"] == "laptop"
    assert body["author_name"] == "Ana"
    assert "canvas_state" not in body
    assert mock.execute.await_args.args[0].limit == 5


def test_should_get_a_revision_with_its_snapshot(client: TestClient) -> None:
    override(get_diagram_revision_factory, REVISION)
    response = client.get(f"{BASE}/{REVISION.id}")
    assert response.status_code == 200
    assert response.json()["canvas_state"] == {"shapes": ["old"]}
    assert response.json()["summary"] == "Added a queue"


def test_should_restore_a_revision_as_its_author(client: TestClient) -> None:
    mock = override(restore_diagram_revision_factory, DIAGRAM)
    track = AsyncMock(spec=TrackAgentActivity)
    app.dependency_overrides[track_agent_activity_factory] = lambda: track
    response = client.post(f"{BASE}/{REVISION.id}/restore", headers={"X-Agent-Name": "Claude"})
    assert response.status_code == 200
    assert response.json()["canvas_state"] == {"shapes": ["old"]}
    params = mock.execute.await_args.args[0]
    assert (params.diagram_id, params.revision_id) == (DIAGRAM.id, REVISION.id)
    assert params.author.origin == RevisionOrigin.AGENT


def test_should_not_let_viewers_restore(client: TestClient) -> None:
    authenticate = AsyncMock(spec=AuthenticateUser)
    authenticate.execute.return_value = ANA
    authorize = AsyncMock(spec=AuthorizeWorkspaceAccess)
    authorize.execute.side_effect = ForbiddenError("This action requires the editor role")
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=True)
    app.dependency_overrides[authenticate_user_factory] = lambda: authenticate
    app.dependency_overrides[authorize_workspace_access_factory] = lambda: authorize
    restore = override(restore_diagram_revision_factory, DIAGRAM)
    response = client.post(
        f"{BASE}/{REVISION.id}/restore", headers={"Authorization": "Bearer good"}
    )
    assert response.status_code == 403
    assert authorize.execute.await_args.args[0].required_role == "editor"
    restore.execute.assert_not_awaited()
