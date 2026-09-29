import time
import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.diagram import Diagram
from app.domain.usecases.diagram.get_diagram import GetDiagram
from app.domain.usecases.presence import track_agent_activity
from app.infra.realtime.connection_manager import manager
from app.main.main import app
from app.presentation.factories.diagram_factories import get_diagram_factory

CLAUDE = {"id": "agent:Claude", "name": "Claude", "kind": "agent"}


@pytest.fixture
def diagram() -> Iterator[Diagram]:
    diagram = Diagram(project_id=uuid.uuid4(), name="Checkout")
    mock_uc = AsyncMock(spec=GetDiagram)
    mock_uc.execute.return_value = diagram
    app.dependency_overrides[get_diagram_factory] = lambda: mock_uc
    yield diagram
    app.dependency_overrides.clear()


def wait_until_gone(diagram_id: str, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if CLAUDE not in manager.participants(diagram_id):
            return True
        time.sleep(0.02)
    return False


@pytest.mark.parametrize("by_link", [False, True])
def test_should_show_agent_to_open_editors_while_it_works(
    diagram: Diagram, monkeypatch: pytest.MonkeyPatch, by_link: bool
) -> None:
    monkeypatch.setattr(track_agent_activity, "AGENT_PRESENCE_SECONDS", 0.2)
    path = (
        f"/diagrams/{diagram.id}"
        if by_link
        else f"/projects/{diagram.project_id}/diagrams/{diagram.id}"
    )
    # The context manager keeps one event loop alive, so the agent's expiry timer can run.
    with TestClient(app) as client, client.websocket_connect(f"/ws/diagrams/{diagram.id}") as ws:
        assert CLAUDE not in ws.receive_json()["users"]
        assert client.get(path, headers={"X-Agent-Name": "Claude"}).status_code == 200
        assert CLAUDE in ws.receive_json()["users"]
        assert wait_until_gone(str(diagram.id))


def test_should_not_show_agent_for_regular_requests(diagram: Diagram) -> None:
    path = f"/projects/{diagram.project_id}/diagrams/{diagram.id}"
    with TestClient(app) as client:
        assert client.get(path).status_code == 200
    assert CLAUDE not in manager.participants(str(diagram.id))
