from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.readiness_probe import ReadinessProbe
from app.domain.errors.domain_errors import ServiceUnavailableError
from app.domain.usecases.health.check_readiness import CheckReadiness, CheckReadinessParams


def make_probe(name: str, ready: bool) -> ReadinessProbe:
    probe = create_autospec(ReadinessProbe, instance=True)
    type(probe).name = name
    probe.is_ready = AsyncMock(return_value=ready)
    return probe  # type: ignore[no-any-return]


@pytest.fixture
def probes() -> list[ReadinessProbe]:
    return [make_probe("database", True), make_probe("cache", True)]


@pytest.fixture
def sut(probes: list[ReadinessProbe]) -> CheckReadiness:
    return CheckReadiness(probes)


async def test_should_pass_when_every_probe_is_ready(sut: CheckReadiness) -> None:
    await sut.execute(CheckReadinessParams())


async def test_should_pass_without_probes() -> None:
    await CheckReadiness([]).execute(CheckReadinessParams())


async def test_should_name_every_failing_probe(probes: list[ReadinessProbe]) -> None:
    sut = CheckReadiness([*probes, make_probe("queue", False), make_probe("storage", False)])
    with pytest.raises(ServiceUnavailableError) as error:
        await sut.execute(CheckReadinessParams())
    assert error.value.message == "Not ready: queue, storage"


async def test_should_check_every_probe(sut: CheckReadiness, probes: list[ReadinessProbe]) -> None:
    await sut.execute(CheckReadinessParams())
    for probe in probes:
        assert isinstance(probe.is_ready, AsyncMock)
        probe.is_ready.assert_awaited_once_with()
