import uuid

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.entities.models.adr import Adr
from app.domain.enums.adr_status import AdrStatus


class CreateAdrParams(InputData):
    diagram_id: uuid.UUID
    title: str
    context: str
    decision: str
    consequences: str
    status: AdrStatus = AdrStatus.PROPOSED


class CreateAdr(Usecase[CreateAdrParams, Adr]):
    def __init__(self, repo: AdrRepository) -> None:
        self._repo = repo

    async def execute(self, params: CreateAdrParams) -> Adr:
        adr = Adr(
            diagram_id=params.diagram_id,
            title=params.title,
            context=params.context,
            decision=params.decision,
            consequences=params.consequences,
            status=params.status,
        )
        return await self._repo.create(adr)
