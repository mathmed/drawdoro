import uuid

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.adr import Adr
from app.domain.enums.adr_status import AdrStatus
from app.domain.errors.domain_errors import NotFoundError


class UpdateAdrParams(InputData):
    adr_id: uuid.UUID
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus


class UpdateAdr(Usecase[UpdateAdrParams, Adr]):
    def __init__(self, repo: AdrRepository) -> None:
        self._repo = repo

    async def execute(self, params: UpdateAdrParams) -> Adr:
        adr = await self._repo.get_by_id(params.adr_id)
        if adr is None:
            raise NotFoundError(f"ADR {params.adr_id} not found")
        adr.title = params.title
        adr.context = params.context
        adr.decision = params.decision
        adr.consequences = params.consequences
        adr.status = params.status
        return await self._repo.update(adr)
