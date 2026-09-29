import uuid
from typing import Any, cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import DrawdoroApi
from tools.diagrams import DiagramTools

PROJECT_ID = uuid.uuid4()
DIAGRAM_ID = uuid.uuid4()
FOLDER_ID = uuid.uuid4()
PATH = f"/projects/{PROJECT_ID}/diagrams/{DIAGRAM_ID}"


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
    return mock


@pytest.fixture
def sut(api: MagicMock) -> DiagramTools:
    return DiagramTools(api)


def test_should_list_diagrams_of_project(sut: DiagramTools, api: MagicMock) -> None:
    api.get_list.return_value = [current_diagram()]
    assert sut.list_diagrams(PROJECT_ID) == [current_diagram()]
    api.get_list.assert_called_once_with(f"/projects/{PROJECT_ID}/diagrams")


def test_should_get_diagram(sut: DiagramTools, api: MagicMock) -> None:
    assert sut.get_diagram(PROJECT_ID, DIAGRAM_ID) == current_diagram()
    api.get_object.assert_called_once_with(PATH)


def test_should_keep_omitted_fields_when_updating_diagram(
    sut: DiagramTools, api: MagicMock
) -> None:
    sut.update_diagram(PROJECT_ID, DIAGRAM_ID, semantic_metadata={"owner": "platform"})
    api.put.assert_called_once_with(
        PATH,
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
        PROJECT_ID,
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
    sut.update_diagram(PROJECT_ID, DIAGRAM_ID, name="Renamed")
    assert api.put.call_args.args[1] == {
        "name": "Renamed",
        "folder_id": None,
        "canvas_state": None,
        "semantic_metadata": {"owner": "payments"},
    }
