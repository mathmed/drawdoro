import uuid
from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
from tools.api import DrawdoroApi
from tools.documentation import DocumentationTools

DIAGRAM_ID = uuid.uuid4()


@pytest.fixture
def api() -> MagicMock:
    return cast(MagicMock, create_autospec(DrawdoroApi, instance=True))


@pytest.fixture
def sut(api: MagicMock) -> DocumentationTools:
    return DocumentationTools(api)


def test_should_get_documentation_of_diagram(sut: DocumentationTools, api: MagicMock) -> None:
    api.get_object.return_value = {"content": "# Checkout"}
    assert sut.get_documentation(DIAGRAM_ID) == {"content": "# Checkout"}
    api.get_object.assert_called_once_with(f"/diagrams/{DIAGRAM_ID}/documentation")


def test_should_replace_documentation_of_diagram(sut: DocumentationTools, api: MagicMock) -> None:
    sut.update_documentation(DIAGRAM_ID, "# Checkout v2")
    api.put.assert_called_once_with(
        f"/diagrams/{DIAGRAM_ID}/documentation", {"content": "# Checkout v2"}
    )
