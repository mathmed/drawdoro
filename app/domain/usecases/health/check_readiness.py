from app.domain.contracts.readiness_probe import ReadinessProbe
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import ServiceUnavailableError


class CheckReadinessParams(InputData):
    pass


class CheckReadiness(Usecase[CheckReadinessParams, None]):
    def __init__(self, probes: list[ReadinessProbe]) -> None:
        self._probes = probes

    async def execute(self, params: CheckReadinessParams) -> None:
        failing = [probe.name for probe in self._probes if not await probe.is_ready()]
        if failing:
            raise ServiceUnavailableError(f"Not ready: {', '.join(failing)}")
