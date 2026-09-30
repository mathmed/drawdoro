from fastapi import APIRouter, Depends

from app.domain.usecases.health.check_readiness import CheckReadiness, CheckReadinessParams
from app.presentation.factories.health_factories import check_readiness_factory

router = APIRouter()


# Liveness: the process answers. It never touches the database, so a database outage does not
# get the pod restarted.
@router.get("/health")
async def health_route() -> dict[str, str]:
    return {"status": "ok"}


# Readiness: the API can serve requests, which needs the database.
@router.get("/ready")
async def ready_route(
    use_case: CheckReadiness = Depends(check_readiness_factory),
) -> dict[str, str]:
    await use_case.execute(CheckReadinessParams())
    return {"status": "ready"}
