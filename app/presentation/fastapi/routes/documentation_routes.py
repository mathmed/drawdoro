from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/diagrams/{diagram_id}/documentation", tags=["documentation"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def get_documentation_page(diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} not implemented")


@router.put("")
async def update_documentation_page(diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} not implemented")
