from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/projects/{project_id}/folders", tags=["folders"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_folders(project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} not implemented")


@router.post("", status_code=201)
async def create_folder(project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} not implemented")


@router.get("/{folder_id}")
async def get_folder(project_id: str, folder_id: str) -> JSONResponse:
    return _not_implemented(f"folder {folder_id} in project {project_id} not implemented")


@router.put("/{folder_id}")
async def update_folder(project_id: str, folder_id: str) -> JSONResponse:
    return _not_implemented(f"folder {folder_id} in project {project_id} not implemented")


@router.delete("/{folder_id}", status_code=204)
async def delete_folder(project_id: str, folder_id: str) -> JSONResponse:
    return _not_implemented(f"folder {folder_id} in project {project_id} not implemented")
