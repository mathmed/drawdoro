import pytest
from caller_key import api_key_from_headers


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        (None, None),
        ({}, None),
        ({"x-api-key": " mcpk_a "}, "mcpk_a"),
        ({"authorization": "Bearer mcpk_b"}, "mcpk_b"),
        ({"authorization": "bearer   mcpk_c"}, "mcpk_c"),
        ({"authorization": "Basic abc"}, None),
        ({"authorization": "Bearer "}, None),
        ({"x-api-key": "mcpk_a", "authorization": "Bearer mcpk_b"}, "mcpk_a"),
    ],
)
def test_should_read_the_callers_key_from_the_headers(
    headers: dict[str, str] | None, expected: str | None
) -> None:
    assert api_key_from_headers(headers) == expected
