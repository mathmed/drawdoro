from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import fixture, mark

from app.domain.errors.domain_errors import (
    ConflictError,
    DomainError,
    InvalidInputError,
    NotFoundError,
    PayloadTooLargeError,
    ServiceUnavailableError,
)
from app.presentation.fastapi.handlers.domain_error_handler import register_error_handlers


@fixture
def client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/raise/{kind}")
    async def raise_error(kind: str) -> None:
        errors: dict[str, type[DomainError]] = {
            "not-found": NotFoundError,
            "conflict": ConflictError,
            "invalid": InvalidInputError,
            "too-large": PayloadTooLargeError,
            "unavailable": ServiceUnavailableError,
        }
        raise errors.get(kind, DomainError)("some message")

    return TestClient(app)


@mark.parametrize(
    ("kind", "status_code"),
    [
        ("not-found", 404),
        ("conflict", 409),
        ("invalid", 422),
        ("too-large", 413),
        ("unavailable", 503),
        ("generic", 400),
    ],
)
def test_should_map_domain_errors_to_http_status(
    client: TestClient, kind: str, status_code: int
) -> None:
    response = client.get(f"/raise/{kind}")
    assert response.status_code == status_code
    assert response.json() == {"detail": "some message"}
