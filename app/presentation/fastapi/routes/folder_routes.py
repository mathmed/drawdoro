import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.folder.create_folder import CreateFolder, CreateFolderParams
from app.domain.usecases.folder.delete_folder import DeleteFolder, DeleteFolderParams
from app.domain.usecases.folder.get_folder import GetFolder, GetFolderParams
from app.domain.usecases.folder.list_folders import ListFolders, ListFoldersParams
from app.domain.usecases.folder.update_folder import UpdateFolder, UpdateFolderParams
from app.presentation.factories.folder_factories import (
    create_folder_factory,
    delete_folder_factory,
    get_folder_factory,
    list_folders_factory,
    update_folder_factory,
)
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.folder_schemas import (
    CreateFolderRequest,
    FolderResponse,
    UpdateFolderRequest,
)

router = APIRouter(
    prefix="/projects/{project_id}/folders",
    tags=["folders"],
    dependencies=[Depends(require_workspace_access)],
)


@router.get("", response_model=list[FolderResponse])
async def list_folders(
    project_id: uuid.UUID,
    use_case: ListFolders = Depends(list_folders_factory),
) -> list[FolderResponse]:
    folders = await use_case.execute(ListFoldersParams(project_id=project_id))
    return [FolderResponse.model_validate(f) for f in folders]


@router.post("", response_model=FolderResponse, status_code=201)
async def create_folder(
    project_id: uuid.UUID,
    body: CreateFolderRequest,
    use_case: CreateFolder = Depends(create_folder_factory),
) -> FolderResponse:
    folder = await use_case.execute(
        CreateFolderParams(
            project_id=project_id, name=body.name, parent_folder_id=body.parent_folder_id
        )
    )
    return FolderResponse.model_validate(folder)


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    project_id: uuid.UUID,
    folder_id: uuid.UUID,
    use_case: GetFolder = Depends(get_folder_factory),
) -> FolderResponse:
    folder = await use_case.execute(GetFolderParams(folder_id=folder_id))
    return FolderResponse.model_validate(folder)


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    project_id: uuid.UUID,
    folder_id: uuid.UUID,
    body: UpdateFolderRequest,
    use_case: UpdateFolder = Depends(update_folder_factory),
) -> FolderResponse:
    folder = await use_case.execute(
        UpdateFolderParams(
            folder_id=folder_id, name=body.name, parent_folder_id=body.parent_folder_id
        )
    )
    return FolderResponse.model_validate(folder)


@router.delete("/{folder_id}", status_code=204)
async def delete_folder(
    project_id: uuid.UUID,
    folder_id: uuid.UUID,
    use_case: DeleteFolder = Depends(delete_folder_factory),
) -> None:
    await use_case.execute(DeleteFolderParams(folder_id=folder_id))
