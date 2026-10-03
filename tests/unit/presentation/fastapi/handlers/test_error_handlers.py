from unittest.mock import MagicMock

import pytest
from fastapi import Request

from app.presentation.fastapi.handlers.domain_error_handler import domain_error_handler
from app.presentation.fastapi.handlers.validation_error_handler import (
    request_validation_error_handler,
)


@pytest.fixture
def http_request() -> Request:
    return MagicMock(spec=Request)


# Each handler is registered for one exception class; any other one must stay unhandled.
async def test_should_leave_other_errors_to_the_domain_handler_caller(
    http_request: Request,
) -> None:
    error = ValueError("not a domain error")
    with pytest.raises(ValueError) as raised:
        await domain_error_handler(http_request, error)
    assert raised.value is error


async def test_should_leave_other_errors_to_the_validation_handler_caller(
    http_request: Request,
) -> None:
    error = ValueError("not a validation error")
    with pytest.raises(ValueError) as raised:
        await request_validation_error_handler(http_request, error)
    assert raised.value is error
