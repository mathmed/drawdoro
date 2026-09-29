import uuid
from typing import Any, cast
from unittest.mock import MagicMock, create_autospec

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from tools.api import DrawdoroApi
from tools.diagrams import DiagramSummary, DiagramTools

PROJECT_ID = uuid.uuid4()
DIAGRAM_ID = uuid.uuid4()
FOLDER_ID = uuid.uuid4()
BY_ID = f"/diagrams/{DIAGRAM_ID}"
IN_PROJECT = f"/projects/{PROJECT_ID}/diagrams/{DIAGRAM_ID}"


def current_diagram() -> dict[str, Any]:
    return {
        "id": str(DIAGRAM_ID),
        "project_id": str(PROJECT_ID),
        "folder_id": str(FOLDER_ID),
        "name": "Checkout",
        "canvas_state": {"shapes": ["box"]},
        "semantic_metadata": {"owner": "payments"},
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    }


@pytest.fixture
def api() -> MagicMock:
    mock = cast(MagicMock, create_autospec(DrawdoroApi, instance=True))
    mock.get_object.return_value = current_diagram()
    mock.put.side_effect = lambda _, body: body
    mock.post.side_effect = lambda _, body: body
    return mock


@pytest.fixture
def sut(api: MagicMock) -> DiagramTools:
    return DiagramTools(api)


def test_should_list_diagrams_without_their_content(sut: DiagramTools, api: MagicMock) -> None:
    api.get_list.return_value = [current_diagram()]
    [summary] = sut.list_diagrams(PROJECT_ID)
    assert summary == DiagramSummary.model_validate(current_diagram())
    assert "canvas_state" not in summary.model_dump()
    api.get_list.assert_called_once_with(f"/projects/{PROJECT_ID}/diagrams")


def test_should_get_diagram_by_id_alone(sut: DiagramTools, api: MagicMock) -> None:
    assert sut.get_diagram(DIAGRAM_ID) == current_diagram()
    api.get_object.assert_called_once_with(BY_ID)


@pytest.mark.parametrize(
    "url",
    [
        f"https://drawdoro.example/diagrams/{DIAGRAM_ID}",
        f"https://drawdoro.example/diagrams/{DIAGRAM_ID}/?tab=docs#top",
        f"  http://localhost:3000/diagrams/{DIAGRAM_ID}\n",
    ],
)
def test_should_open_editor_links(sut: DiagramTools, api: MagicMock, url: str) -> None:
    assert sut.open_link(url) == current_diagram()
    api.get_object.assert_called_once_with(BY_ID)


def test_should_open_share_links(sut: DiagramTools, api: MagicMock) -> None:
    sut.open_link("https://drawdoro.example/share/Ab-9_xY")
    api.get_object.assert_called_once_with("/share/Ab-9_xY")


@pytest.mark.parametrize(
    "url",
    [
        "https://drawdoro.example/",
        "https://drawdoro.example/diagrams/not-a-uuid",
        "https://drawdoro.example/share/..%2Fworkspaces",
        f"https://drawdoro.example/diagrams/{DIAGRAM_ID}/comments",
    ],
)
def test_should_reject_links_that_are_not_diagrams(
    sut: DiagramTools, api: MagicMock, url: str
) -> None:
    with pytest.raises(ToolError):
        sut.open_link(url)
    api.get_object.assert_not_called()


def test_should_create_diagram(sut: DiagramTools, api: MagicMock) -> None:
    sut.create_diagram(PROJECT_ID, "Payments", folder_id=FOLDER_ID)
    api.post.assert_called_once_with(
        f"/projects/{PROJECT_ID}/diagrams",
        {"name": "Payments", "folder_id": str(FOLDER_ID), "canvas_state": None},
    )


def test_should_keep_omitted_fields_when_updating_diagram(
    sut: DiagramTools, api: MagicMock
) -> None:
    sut.update_diagram(DIAGRAM_ID, semantic_metadata={"owner": "platform"})
    api.get_object.assert_called_once_with(BY_ID)
    api.put.assert_called_once_with(
        IN_PROJECT,
        {
            "name": "Checkout",
            "folder_id": str(FOLDER_ID),
            "canvas_state": {"shapes": ["box"]},
            "semantic_metadata": {"owner": "platform"},
        },
    )


def test_should_apply_every_given_field_when_updating_diagram(
    sut: DiagramTools, api: MagicMock
) -> None:
    new_folder_id = uuid.uuid4()
    result = sut.update_diagram(
        DIAGRAM_ID,
        name="Checkout v2",
        folder_id=new_folder_id,
        canvas_state={"shapes": []},
        semantic_metadata={},
    )
    assert result == {
        "name": "Checkout v2",
        "folder_id": str(new_folder_id),
        "canvas_state": {"shapes": []},
        "semantic_metadata": {},
    }


def test_should_keep_null_fields_null_when_updating_diagram(
    sut: DiagramTools, api: MagicMock
) -> None:
    api.get_object.return_value = current_diagram() | {"folder_id": None, "canvas_state": None}
    sut.update_diagram(DIAGRAM_ID, name="Renamed")
    assert api.put.call_args.args[1] == {
        "name": "Renamed",
        "folder_id": None,
        "canvas_state": None,
        "semantic_metadata": {"owner": "payments"},
    }
