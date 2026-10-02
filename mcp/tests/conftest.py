from typing import Any

import pytest

from tests.tldraw_records import sample_canvas_state


@pytest.fixture
def canvas_state() -> dict[str, Any]:
    return sample_canvas_state()
