from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_workspaces() -> JSONResponse:
    return _not_implemented()


@router.post("", status_code=201)
async def create_workspace() -> JSONResponse:
    return _not_implemented()


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str) -> JSONResponse:
    return _not_implemented(f"workspace {workspace_id} not implemented")


@router.put("/{workspace_id}")
async def update_workspace(workspace_id: str) -> JSONResponse:
    return _not_implemented(f"workspace {workspace_id} not implemented")


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(workspace_id: str) -> JSONResponse:
    return _not_implemented(f"workspace {workspace_id} not implemented")
