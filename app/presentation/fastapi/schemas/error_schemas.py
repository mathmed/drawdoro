from typing import Any

from pydantic import BaseModel


# Body of the errors raised by the domain (see handlers/domain_error_handler.py).
class ErrorResponse(BaseModel):
    detail: str


# Documents a domain error a route can answer with, for its `responses=`.
def error_response(status_code: int, description: str) -> dict[int | str, dict[str, Any]]:
    return {status_code: {"model": ErrorResponse, "description": description}}
