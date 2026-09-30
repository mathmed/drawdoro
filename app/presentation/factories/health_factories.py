from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.health.check_readiness import CheckReadiness
from app.infra.database.database_readiness_probe import DatabaseReadinessProbe
from app.infra.database.session import get_session


async def check_readiness_factory(session: AsyncSession = Depends(get_session)) -> CheckReadiness:
    return CheckReadiness([DatabaseReadinessProbe(session)])
