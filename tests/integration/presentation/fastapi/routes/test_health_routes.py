from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.errors.domain_errors import ServiceUnavailableError
from app.domain.usecases.health.check_readiness import CheckReadiness
from app.main.main import app
from app.presentation.factories.health_factories import check_readiness_factory


@pytest.fixture
def check_readiness() -> Iterator[AsyncMock]:
    use_case = AsyncMock(spec=CheckReadiness)
    app.dependency_overrides[check_readiness_factory] = lambda: use_case
    yield use_case
    app.dependency_overrides.clear()


@pytest.fixture
def sut() -> TestClient:
    return TestClient(app)


def test_should_return_ok(sut: TestClient) -> None:
    response = sut.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_should_keep_health_away_from_the_database(
    sut: TestClient, check_readiness: AsyncMock
) -> None:
    check_readiness.execute.side_effect = ServiceUnavailableError("Not ready: database")
    assert sut.get("/health").status_code == 200
    check_readiness.execute.assert_not_awaited()


def test_should_return_ready_when_dependencies_answer(
    sut: TestClient, check_readiness: AsyncMock
) -> None:
    response = sut.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    check_readiness.execute.assert_awaited_once()


def test_should_return_503_when_a_dependency_is_down(
    sut: TestClient, check_readiness: AsyncMock
) -> None:
    check_readiness.execute.side_effect = ServiceUnavailableError("Not ready: database")
    response = sut.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"detail": "Not ready: database"}
