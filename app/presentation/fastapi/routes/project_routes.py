from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/workspaces/{workspace_id}/projects", tags=["projects"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_projects(workspace_id: str) -> JSONResponse:
    return _not_implemented(f"workspace {workspace_id} not implemented")


@router.post("", status_code=201)
async def create_project(workspace_id: str) -> JSONResponse:
    return _not_implemented(f"workspace {workspace_id} not implemented")


@router.get("/{project_id}")
async def get_project(workspace_id: str, project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} in workspace {workspace_id} not implemented")


@router.put("/{project_id}")
async def update_project(workspace_id: str, project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} in workspace {workspace_id} not implemented")


@router.delete("/{project_id}", status_code=204)
async def delete_project(workspace_id: str, project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} in workspace {workspace_id} not implemented")
