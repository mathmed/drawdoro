from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import BackendApi
from tools.workspaces import WorkspaceTools


@pytest.fixture
def api() -> MagicMock:
    return cast(MagicMock, create_autospec(BackendApi, instance=True))


@pytest.fixture
def sut(api: MagicMock) -> WorkspaceTools:
    return WorkspaceTools(api)


def test_should_list_workspaces(sut: WorkspaceTools, api: MagicMock) -> None:
    api.get_list.return_value = [{"id": "w1"}]
    assert sut.list_workspaces() == [{"id": "w1"}]
    api.get_list.assert_called_once_with("/workspaces")
