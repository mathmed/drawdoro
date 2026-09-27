from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/templates", tags=["templates"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_templates() -> JSONResponse:
    return _not_implemented()


@router.post("", status_code=201)
async def create_template() -> JSONResponse:
    return _not_implemented()


@router.get("/{template_id}")
async def get_template(template_id: str) -> JSONResponse:
    return _not_implemented(f"template {template_id} not implemented")


@router.put("/{template_id}")
async def update_template(template_id: str) -> JSONResponse:
    return _not_implemented(f"template {template_id} not implemented")


@router.delete("/{template_id}", status_code=204)
async def delete_template(template_id: str) -> JSONResponse:
    return _not_implemented(f"template {template_id} not implemented")
