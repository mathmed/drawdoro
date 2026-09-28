import uuid

from fastapi import APIRouter, Depends

from app.domain.entities.models.user import User
from app.domain.usecases.workspace.create_workspace import CreateWorkspace, CreateWorkspaceParams
from app.domain.usecases.workspace.delete_workspace import DeleteWorkspace, DeleteWorkspaceParams
from app.domain.usecases.workspace.get_workspace import GetWorkspace, GetWorkspaceParams
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces, ListWorkspacesParams
from app.domain.usecases.workspace.update_workspace import UpdateWorkspace, UpdateWorkspaceParams
from app.presentation.factories.workspace_factories import (
    create_workspace_factory,
    delete_workspace_factory,
    get_workspace_factory,
    list_workspaces_factory,
    update_workspace_factory,
)
from app.presentation.fastapi.dependencies.current_user import get_current_user
from app.presentation.fastapi.dependencies.workspace_access import (
    require_workspace_access,
    require_workspace_owner,
)
from app.presentation.fastapi.schemas.workspace_schemas import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    WorkspaceResponse,
)

router = APIRouter(
    prefix="/workspaces", tags=["workspaces"], dependencies=[Depends(require_workspace_access)]
)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    use_case: ListWorkspaces = Depends(list_workspaces_factory),
    user: User | None = Depends(get_current_user),
) -> list[WorkspaceResponse]:
    workspaces = await use_case.execute(
        ListWorkspacesParams(user_id=user.id if user is not None else None)
    )
    return [WorkspaceResponse.model_validate(w) for w in workspaces]


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    body: CreateWorkspaceRequest,
    use_case: CreateWorkspace = Depends(create_workspace_factory),
    user: User | None = Depends(get_current_user),
) -> WorkspaceResponse:
    workspace = await use_case.execute(
        CreateWorkspaceParams(
            name=body.name, slug=body.slug, creator_id=user.id if user is not None else None
        )
    )
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    use_case: GetWorkspace = Depends(get_workspace_factory),
) -> WorkspaceResponse:
    workspace = await use_case.execute(GetWorkspaceParams(workspace_id=workspace_id))
    return WorkspaceResponse.model_validate(workspace)


@router.put(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
    dependencies=[Depends(require_workspace_owner)],
)
async def update_workspace(
    workspace_id: uuid.UUID,
    body: UpdateWorkspaceRequest,
    use_case: UpdateWorkspace = Depends(update_workspace_factory),
) -> WorkspaceResponse:
    workspace = await use_case.execute(
        UpdateWorkspaceParams(workspace_id=workspace_id, name=body.name, slug=body.slug)
    )
    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=204, dependencies=[Depends(require_workspace_owner)])
async def delete_workspace(
    workspace_id: uuid.UUID,
    use_case: DeleteWorkspace = Depends(delete_workspace_factory),
) -> None:
    await use_case.execute(DeleteWorkspaceParams(workspace_id=workspace_id))
