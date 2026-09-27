import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.adr.create_adr import CreateAdr, CreateAdrParams
from app.domain.usecases.adr.delete_adr import DeleteAdr, DeleteAdrParams
from app.domain.usecases.adr.get_adr import GetAdr, GetAdrParams
from app.domain.usecases.adr.list_adrs import ListAdrs, ListAdrsParams
from app.domain.usecases.adr.update_adr import UpdateAdr, UpdateAdrParams
from app.presentation.factories.adr_factories import (
    create_adr_factory,
    delete_adr_factory,
    get_adr_factory,
    list_adrs_factory,
    update_adr_factory,
)
from app.presentation.fastapi.schemas.adr_schemas import (
    AdrResponse,
    CreateAdrRequest,
    UpdateAdrRequest,
)

router = APIRouter(prefix="/diagrams/{diagram_id}/adrs", tags=["adrs"])


@router.get("", response_model=list[AdrResponse])
async def list_adrs(
    diagram_id: uuid.UUID,
    use_case: ListAdrs = Depends(list_adrs_factory),
) -> list[AdrResponse]:
    adrs = await use_case.execute(ListAdrsParams(diagram_id=diagram_id))
    return [AdrResponse.model_validate(a) for a in adrs]


@router.post("", response_model=AdrResponse, status_code=201)
async def create_adr(
    diagram_id: uuid.UUID,
    body: CreateAdrRequest,
    use_case: CreateAdr = Depends(create_adr_factory),
) -> AdrResponse:
    adr = await use_case.execute(
        CreateAdrParams(
            diagram_id=diagram_id,
            title=body.title,
            context=body.context,
            decision=body.decision,
            consequences=body.consequences,
            status=body.status,
        )
    )
    return AdrResponse.model_validate(adr)


@router.get("/{adr_id}", response_model=AdrResponse)
async def get_adr(
    diagram_id: uuid.UUID,
    adr_id: uuid.UUID,
    use_case: GetAdr = Depends(get_adr_factory),
) -> AdrResponse:
    adr = await use_case.execute(GetAdrParams(adr_id=adr_id))
    return AdrResponse.model_validate(adr)


@router.put("/{adr_id}", response_model=AdrResponse)
async def update_adr(
    diagram_id: uuid.UUID,
    adr_id: uuid.UUID,
    body: UpdateAdrRequest,
    use_case: UpdateAdr = Depends(update_adr_factory),
) -> AdrResponse:
    adr = await use_case.execute(
        UpdateAdrParams(
            adr_id=adr_id,
            title=body.title,
            context=body.context,
            decision=body.decision,
            consequences=body.consequences,
            status=body.status,
        )
    )
    return AdrResponse.model_validate(adr)


@router.delete("/{adr_id}", status_code=204)
async def delete_adr(
    diagram_id: uuid.UUID,
    adr_id: uuid.UUID,
    use_case: DeleteAdr = Depends(delete_adr_factory),
) -> None:
    await use_case.execute(DeleteAdrParams(adr_id=adr_id))
