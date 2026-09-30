import uuid
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import MagicMock, create_autospec

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from tools.api import BackendApi
from tools.diagrams import DiagramSaved, DiagramSummary, DiagramTools, ShapeEdits

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
    mock = cast(MagicMock, create_autospec(BackendApi, instance=True))
    mock.get_object.return_value = current_diagram()
    mock.put.side_effect = lambda _, body: current_diagram() | body
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
        f"https://diagrams.example/diagrams/{DIAGRAM_ID}",
        f"https://diagrams.example/diagrams/{DIAGRAM_ID}/?tab=docs#top",
        f"  http://localhost:3000/diagrams/{DIAGRAM_ID}\n",
    ],
)
def test_should_open_editor_links(sut: DiagramTools, api: MagicMock, url: str) -> None:
    assert sut.open_link(url) == current_diagram()
    api.get_object.assert_called_once_with(BY_ID)


def test_should_open_share_links(sut: DiagramTools, api: MagicMock) -> None:
    sut.open_link("https://diagrams.example/share/Ab-9_xY")
    api.get_object.assert_called_once_with("/share/Ab-9_xY")


@pytest.mark.parametrize(
    "url",
    [
        "https://diagrams.example/",
        "https://diagrams.example/diagrams/not-a-uuid",
        "https://diagrams.example/share/..%2Fworkspaces",
        f"https://diagrams.example/diagrams/{DIAGRAM_ID}/comments",
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
            "revision_summary": "Updated semantic_metadata",
        },
    )


def test_should_apply_every_given_field_when_updating_diagram(
    sut: DiagramTools, api: MagicMock
) -> None:
    new_folder_id = uuid.uuid4()
    sut.update_diagram(
        DIAGRAM_ID,
        name="Checkout v2",
        folder_id=new_folder_id,
        canvas_state={"shapes": []},
        semantic_metadata={},
    )
    assert api.put.call_args.args[1] == {
        "name": "Checkout v2",
        "folder_id": str(new_folder_id),
        "canvas_state": {"shapes": []},
        "semantic_metadata": {},
        "revision_summary": "Updated name, folder_id, canvas_state, semantic_metadata",
    }


def test_should_answer_update_without_echoing_the_canvas(sut: DiagramTools) -> None:
    result = sut.update_diagram(DIAGRAM_ID, canvas_state={"store": {"shape:a": {}}, "schema": {}})
    assert result == DiagramSaved(
        id=DIAGRAM_ID,
        name="Checkout",
        updated_at=datetime(2026, 9, 1, tzinfo=UTC),
        records=1,
    )


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
        "revision_summary": "Updated name",
    }


@pytest.fixture
def api_with_canvas(api: MagicMock, canvas_state: dict[str, Any]) -> MagicMock:
    api.get_object.return_value = current_diagram() | {"canvas_state": canvas_state}
    return api


def test_should_save_only_the_edited_records_into_the_canvas(
    sut: DiagramTools, api_with_canvas: MagicMock, canvas_state: dict[str, Any]
) -> None:
    result = sut.edit_shapes(
        DIAGRAM_ID,
        upsert=[{"id": "shape:api", "meta": {"fontSize": 20}}],
        delete=["shape:line"],
    )
    body = api_with_canvas.put.call_args.args[1]
    assert api_with_canvas.put.call_args.args[0] == IN_PROJECT
    assert body["name"] == "Checkout"
    assert body["semantic_metadata"] == {"owner": "payments"}
    store = body["canvas_state"]["store"]
    assert store["shape:api"]["meta"]["fontSize"] == 20
    assert "shape:line" not in store
    assert store["shape:db"] == canvas_state["store"]["shape:db"]
    assert body["canvas_state"]["schema"] == canvas_state["schema"]
    assert result == ShapeEdits(
        id=DIAGRAM_ID,
        name="Checkout",
        updated_at=datetime(2026, 9, 1, tzinfo=UTC),
        records=len(canvas_state["store"]) - 1,
        created=[],
        changed=["shape:api"],
        deleted=["shape:line"],
    )


@pytest.mark.parametrize(
    "expected_updated_at",
    [datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 1)],
)
def test_should_edit_when_the_diagram_is_still_the_version_read(
    sut: DiagramTools, api_with_canvas: MagicMock, expected_updated_at: datetime
) -> None:
    sut.edit_shapes(DIAGRAM_ID, delete=["shape:line"], expected_updated_at=expected_updated_at)
    api_with_canvas.put.assert_called_once()


def test_should_not_edit_a_diagram_saved_after_it_was_read(
    sut: DiagramTools, api_with_canvas: MagicMock
) -> None:
    with pytest.raises(ToolError, match="read it again"):
        sut.edit_shapes(
            DIAGRAM_ID, delete=["shape:line"], expected_updated_at=datetime(2026, 8, 31, tzinfo=UTC)
        )
    api_with_canvas.put.assert_not_called()


def test_should_ask_for_something_to_edit(sut: DiagramTools, api: MagicMock) -> None:
    with pytest.raises(ToolError):
        sut.edit_shapes(DIAGRAM_ID)
    api.get_object.assert_not_called()


def test_should_outline_a_diagram(sut: DiagramTools, api_with_canvas: MagicMock) -> None:
    outline = sut.get_diagram_outline(DIAGRAM_ID)
    api_with_canvas.get_object.assert_called_once_with(BY_ID)
    assert (outline.id, outline.name, outline.project_id) == (DIAGRAM_ID, "Checkout", PROJECT_ID)
    assert [shape.id for shape in outline.shapes][:2] == ["shape:frame", "shape:inside"]


def test_should_record_the_agents_summary_in_the_history(sut: DiagramTools, api: MagicMock) -> None:
    sut.update_diagram(DIAGRAM_ID, name="Checkout v2", summary="Renamed after the split")
    assert api.put.call_args.args[1]["revision_summary"] == "Renamed after the split"


def test_should_cap_the_summary_to_what_the_api_accepts(sut: DiagramTools, api: MagicMock) -> None:
    sut.update_diagram(DIAGRAM_ID, name="Checkout v2", summary="x" * 1000)
    assert len(api.put.call_args.args[1]["revision_summary"]) == 500


def test_should_describe_shape_edits_when_no_summary_is_given(
    sut: DiagramTools, api_with_canvas: MagicMock, canvas_state: dict[str, Any]
) -> None:
    shape_id = next(key for key in canvas_state["store"] if key.startswith("shape:"))
    result = sut.edit_shapes(DIAGRAM_ID, delete=[shape_id])
    expected = f"Edited the canvas: {len(result.deleted)} deleted"
    assert api_with_canvas.put.call_args.args[1]["revision_summary"] == expected


def test_should_pass_the_summary_of_shape_edits(
    sut: DiagramTools, api_with_canvas: MagicMock, canvas_state: dict[str, Any]
) -> None:
    shape_id = next(key for key in canvas_state["store"] if key.startswith("shape:"))
    sut.edit_shapes(DIAGRAM_ID, delete=[shape_id], summary="Removed the legacy cache")
    assert api_with_canvas.put.call_args.args[1]["revision_summary"] == "Removed the legacy cache"
