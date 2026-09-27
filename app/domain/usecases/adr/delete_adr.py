import uuid

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.errors.domain_errors import NotFoundError


class DeleteAdrParams(InputData):
    adr_id: uuid.UUID


class DeleteAdr(Usecase[DeleteAdrParams, None]):
    def __init__(self, repo: AdrRepository) -> None:
        self._repo = repo

    async def execute(self, params: DeleteAdrParams) -> None:
        adr = await self._repo.get_by_id(params.adr_id)
        if adr is None:
            raise NotFoundError(f"ADR {params.adr_id} not found")
        await self._repo.delete(params.adr_id)
