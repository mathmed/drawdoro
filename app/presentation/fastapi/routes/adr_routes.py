from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/diagrams/{diagram_id}/adrs", tags=["adrs"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_adrs(diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} not implemented")


@router.post("", status_code=201)
async def create_adr(diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} not implemented")


@router.get("/{adr_id}")
async def get_adr(diagram_id: str, adr_id: str) -> JSONResponse:
    return _not_implemented(f"adr {adr_id} in diagram {diagram_id} not implemented")


@router.put("/{adr_id}")
async def update_adr(diagram_id: str, adr_id: str) -> JSONResponse:
    return _not_implemented(f"adr {adr_id} in diagram {diagram_id} not implemented")


@router.delete("/{adr_id}", status_code=204)
async def delete_adr(diagram_id: str, adr_id: str) -> JSONResponse:
    return _not_implemented(f"adr {adr_id} in diagram {diagram_id} not implemented")
