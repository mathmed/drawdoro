from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/diagrams/{diagram_id}/comments", tags=["comments"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_comments(diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} not implemented")


@router.post("", status_code=201)
async def create_comment(diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} not implemented")
