import uuid
from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import DrawdoroApi
from tools.comments import CommentTools


@pytest.fixture
def api() -> MagicMock:
    return cast(MagicMock, create_autospec(DrawdoroApi, instance=True))


@pytest.fixture
def sut(api: MagicMock) -> CommentTools:
    return CommentTools(api)


def test_should_list_comments_of_diagram(sut: CommentTools, api: MagicMock) -> None:
    diagram_id = uuid.uuid4()
    api.get_list.return_value = [{"element_id": "shape:a"}]
    assert sut.list_comments(diagram_id) == [{"element_id": "shape:a"}]
    api.get_list.assert_called_once_with(f"/diagrams/{diagram_id}/comments")
