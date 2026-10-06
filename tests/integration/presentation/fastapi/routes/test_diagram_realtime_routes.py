import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock, create_autospec

import pytest
from fastapi.testclient import TestClient

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.revision_recorder import RevisionRecorder
from app.domain.usecases.diagram.get_diagram_location import GetDiagramLocation
from app.domain.usecases.diagram.update_diagram import UpdateDiagram, UpdateDiagramParams
from app.domain.usecases.presence.track_agent_activity import TrackAgentActivity
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_diagram_update_notifier import RealtimeDiagramUpdateNotifier
from app.main.main import app
from app.presentation.factories.diagram_factories import (
    get_diagram_location_factory,
    update_diagram_factory,
)
from app.presentation.factories.presence_factories import track_agent_activity_factory
from tests.doubles import double


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.fixture
def diagram() -> Diagram:
    return Diagram(project_id=uuid.uuid4(), name="Checkout", canvas_state={"shapes": ["box"]})


def use_case_with_mocked_execute(diagram: Diagram) -> AsyncMock:
    mock_uc = AsyncMock(spec=UpdateDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[update_diagram_factory] = lambda: mock_uc
    return mock_uc


def test_should_pass_client_id_header_to_use_case(client: TestClient, diagram: Diagram) -> None:
    mock_uc = use_case_with_mocked_execute(diagram)
    response = client.put(
        f"/projects/{diagram.project_id}/diagrams/{diagram.id}",
        json={"name": "Checkout"},
        headers={"X-Client-Id": "tab-1"},
    )
    assert response.status_code == 200
    params: UpdateDiagramParams = mock_uc.execute.await_args.args[0]
    assert params.origin_client_id == "tab-1"


def test_should_leave_origin_empty_without_client_id_header(
    client: TestClient, diagram: Diagram
) -> None:
    mock_uc = use_case_with_mocked_execute(diagram)
    client.put(f"/projects/{diagram.project_id}/diagrams/{diagram.id}", json={"name": "Checkout"})
    params: UpdateDiagramParams = mock_uc.execute.await_args.args[0]
    assert params.origin_client_id is None


def test_should_reject_oversized_client_id(client: TestClient, diagram: Diagram) -> None:
    use_case_with_mocked_execute(diagram)
    response = client.put(
        f"/projects/{diagram.project_id}/diagrams/{diagram.id}",
        json={"name": "Checkout"},
        headers={"X-Client-Id": "x" * 65},
    )
    assert response.status_code == 422


def test_should_push_saved_diagram_to_open_editors(client: TestClient, diagram: Diagram) -> None:
    repo = double(DiagramRepository)
    repo.get_by_id.return_value = diagram
    repo.update.side_effect = lambda updated: updated
    app.dependency_overrides[update_diagram_factory] = lambda: UpdateDiagram(
        repo,
        RealtimeDiagramUpdateNotifier(manager),
        create_autospec(RevisionRecorder, instance=True),
    )
    locate = AsyncMock(spec=GetDiagramLocation)
    locate.execute.side_effect = NotFoundError("Diagram not found")
    app.dependency_overrides[get_diagram_location_factory] = lambda: locate
    with client.websocket_connect(f"/ws/diagrams/{diagram.id}") as editor:
        assert editor.receive_json()["type"] == "presence"
        response = client.put(
            f"/projects/{diagram.project_id}/diagrams/{diagram.id}",
            json={"name": "Checkout v2", "canvas_state": {"shapes": ["box", "arrow"]}},
        )
        assert response.status_code == 200
        message = editor.receive_json()
    assert message["type"] == "diagram_updated"
    assert message["client_id"] is None
    assert message["diagram"]["name"] == "Checkout v2"
    assert message["diagram"]["canvas_state"] == {"shapes": ["box", "arrow"]}


def test_should_record_agent_changes_with_their_summary(
    client: TestClient, diagram: Diagram
) -> None:
    mock_uc = use_case_with_mocked_execute(diagram)
    track = AsyncMock(spec=TrackAgentActivity)
    app.dependency_overrides[track_agent_activity_factory] = lambda: track
    response = client.put(
        f"/projects/{diagram.project_id}/diagrams/{diagram.id}",
        json={"name": "Checkout", "revision_summary": "Added the payment queue"},
        headers={"X-Agent-Name": "Claude"},
    )
    assert response.status_code == 200
    params = mock_uc.execute.await_args.args[0]
    assert params.revision_summary == "Added the payment queue"
    assert params.author == RevisionAuthor(origin=RevisionOrigin.AGENT, agent_name="Claude")


def test_should_record_editor_saves_as_human_changes(client: TestClient, diagram: Diagram) -> None:
    mock_uc = use_case_with_mocked_execute(diagram)
    response = client.put(
        f"/projects/{diagram.project_id}/diagrams/{diagram.id}", json={"name": "Checkout"}
    )
    assert response.status_code == 200
    assert mock_uc.execute.await_args.args[0].author == RevisionAuthor()
