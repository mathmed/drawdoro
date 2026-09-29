import uuid
from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import BackendApi
from tools.folders import FolderTools

PROJECT_ID = uuid.uuid4()


@pytest.fixture
def api() -> MagicMock:
    mock = cast(MagicMock, create_autospec(BackendApi, instance=True))
    mock.post.side_effect = lambda _, body: body
    return mock


@pytest.fixture
def sut(api: MagicMock) -> FolderTools:
    return FolderTools(api)


def test_should_list_folders_of_project(sut: FolderTools, api: MagicMock) -> None:
    api.get_list.return_value = [{"id": "f1"}]
    assert sut.list_folders(PROJECT_ID) == [{"id": "f1"}]
    api.get_list.assert_called_once_with(f"/projects/{PROJECT_ID}/folders")


def test_should_create_top_level_folder(sut: FolderTools, api: MagicMock) -> None:
    sut.create_folder(PROJECT_ID, "Backend")
    api.post.assert_called_once_with(
        f"/projects/{PROJECT_ID}/folders", {"name": "Backend", "parent_folder_id": None}
    )


def test_should_create_nested_folder(sut: FolderTools, api: MagicMock) -> None:
    parent_id = uuid.uuid4()
    assert sut.create_folder(PROJECT_ID, "Queues", parent_folder_id=parent_id) == {
        "name": "Queues",
        "parent_folder_id": str(parent_id),
    }
