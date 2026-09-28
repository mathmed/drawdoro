import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.project.create_project import CreateProject, CreateProjectParams
from app.domain.usecases.project.delete_project import DeleteProject, DeleteProjectParams
from app.domain.usecases.project.get_project import GetProject, GetProjectParams
from app.domain.usecases.project.list_projects import ListProjects, ListProjectsParams
from app.domain.usecases.project.update_project import UpdateProject, UpdateProjectParams
from app.presentation.factories.project_factories import (
    create_project_factory,
    delete_project_factory,
    get_project_factory,
    list_projects_factory,
    update_project_factory,
)
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.project_schemas import (
    CreateProjectRequest,
    ProjectResponse,
    UpdateProjectRequest,
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["projects"],
    dependencies=[Depends(require_workspace_access)],
)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: uuid.UUID,
    use_case: ListProjects = Depends(list_projects_factory),
) -> list[ProjectResponse]:
    projects = await use_case.execute(ListProjectsParams(workspace_id=workspace_id))
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    workspace_id: uuid.UUID,
    body: CreateProjectRequest,
    use_case: CreateProject = Depends(create_project_factory),
) -> ProjectResponse:
    project = await use_case.execute(
        CreateProjectParams(workspace_id=workspace_id, name=body.name, description=body.description)
    )
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    use_case: GetProject = Depends(get_project_factory),
) -> ProjectResponse:
    project = await use_case.execute(GetProjectParams(project_id=project_id))
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    body: UpdateProjectRequest,
    use_case: UpdateProject = Depends(update_project_factory),
) -> ProjectResponse:
    project = await use_case.execute(
        UpdateProjectParams(project_id=project_id, name=body.name, description=body.description)
    )
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    use_case: DeleteProject = Depends(delete_project_factory),
) -> None:
    await use_case.execute(DeleteProjectParams(project_id=project_id))
