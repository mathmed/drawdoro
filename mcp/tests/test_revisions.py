import uuid
from datetime import UTC, datetime
from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import BackendApi
from tools.revisions import (
    RestoredDiagram,
    RevisionOrigin,
    RevisionTools,
)

DIAGRAM_ID = uuid.uuid4()
REVISION_ID = uuid.uuid4()
REVISION = {
    "id": str(REVISION_ID),
    "diagram_id": str(DIAGRAM_ID),
    "kind": "edit",
    "origin": "agent",
    "author_id": str(uuid.uuid4()),
    "author_name": "Ana",
    "author_picture_url": None,
    "agent_name": "Claude",
    "agent_label": "laptop",
    "summary": "Added a queue",
    "restored_from_id": None,
    "created_at": "2026-09-29T10:00:00Z",
    "updated_at": "2026-09-29T10:00:00",
}


@pytest.fixture
def api() -> MagicMock:
    mock = cast(MagicMock, create_autospec(BackendApi, instance=True))
    mock.get_list.return_value = [REVISION]
    mock.post.return_value = {
        "id": str(DIAGRAM_ID),
        "name": "Checkout",
        "updated_at": "2026-09-29T11:00:00",
        "canvas_state": {"store": {}},
    }
    return mock


@pytest.fixture
def sut(api: MagicMock) -> RevisionTools:
    return RevisionTools(api)


def test_should_list_who_changed_the_diagram(sut: RevisionTools, api: MagicMock) -> None:
    [revision] = sut.list_revisions(DIAGRAM_ID, limit=5)
    assert revision.origin == RevisionOrigin.AGENT
    assert (revision.author_name, revision.agent_label) == ("Ana", "laptop")
    assert revision.updated_at.tzinfo is not None
    api.get_list.assert_called_once_with(f"/diagrams/{DIAGRAM_ID}/revisions?limit=5")


@pytest.mark.parametrize(("limit", "sent"), [(0, 1), (5000, 200)])
def test_should_keep_the_limit_within_range(
    sut: RevisionTools, api: MagicMock, limit: int, sent: int
) -> None:
    sut.list_revisions(DIAGRAM_ID, limit=limit)
    api.get_list.assert_called_once_with(f"/diagrams/{DIAGRAM_ID}/revisions?limit={sent}")


def test_should_restore_without_echoing_the_canvas(sut: RevisionTools, api: MagicMock) -> None:
    result = sut.restore_revision(DIAGRAM_ID, REVISION_ID)
    assert result == RestoredDiagram(
        id=DIAGRAM_ID,
        name="Checkout",
        updated_at=datetime(2026, 9, 29, 11, tzinfo=UTC),
        restored_from_id=REVISION_ID,
    )
    api.post.assert_called_once_with(f"/diagrams/{DIAGRAM_ID}/revisions/{REVISION_ID}/restore", {})
