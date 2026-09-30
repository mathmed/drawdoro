import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.contracts.readiness_probe import ReadinessProbe

logger = logging.getLogger(__name__)

# Below the usual readiness probe timeout, so an unreachable database answers 503 instead of
# leaving the probe hanging.
READINESS_TIMEOUT_SECONDS = 2.0


class DatabaseReadinessProbe(ReadinessProbe):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def name(self) -> str:
        return "database"

    async def is_ready(self) -> bool:
        try:
            async with asyncio.timeout(READINESS_TIMEOUT_SECONDS):
                await self._session.execute(text("SELECT 1"))
        except (SQLAlchemyError, OSError, TimeoutError) as error:
            logger.warning("database readiness check failed: %s", error)
            return False
        return True
