from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/projects/{project_id}/diagrams", tags=["diagrams"])


def _not_implemented(detail: str = "not implemented") -> JSONResponse:
    return JSONResponse(status_code=501, content={"detail": detail})


@router.get("")
async def list_diagrams(project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} not implemented")


@router.post("", status_code=201)
async def create_diagram(project_id: str) -> JSONResponse:
    return _not_implemented(f"project {project_id} not implemented")


@router.get("/{diagram_id}")
async def get_diagram(project_id: str, diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} in project {project_id} not implemented")


@router.put("/{diagram_id}")
async def update_diagram(project_id: str, diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} in project {project_id} not implemented")


@router.delete("/{diagram_id}", status_code=204)
async def delete_diagram(project_id: str, diagram_id: str) -> JSONResponse:
    return _not_implemented(f"diagram {diagram_id} in project {project_id} not implemented")
