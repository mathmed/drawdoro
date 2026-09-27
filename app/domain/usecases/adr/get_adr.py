import uuid

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.adr import Adr
from app.domain.errors.domain_errors import NotFoundError


class GetAdrParams(InputData):
    adr_id: uuid.UUID


class GetAdr(Usecase[GetAdrParams, Adr]):
    def __init__(self, repo: AdrRepository) -> None:
        self._repo = repo

    async def execute(self, params: GetAdrParams) -> Adr:
        adr = await self._repo.get_by_id(params.adr_id)
        if adr is None:
            raise NotFoundError(f"ADR {params.adr_id} not found")
        return adr
