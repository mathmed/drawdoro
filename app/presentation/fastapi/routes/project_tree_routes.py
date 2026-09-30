import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.project.get_project_tree import GetProjectTree, GetProjectTreeParams
from app.presentation.factories.project_factories import get_project_tree_factory
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.project_tree_schemas import ProjectTreeResponse

router = APIRouter(
    prefix="/projects/{project_id}/tree",
    tags=["projects"],
    dependencies=[Depends(require_workspace_access)],
)


@router.get("", response_model=ProjectTreeResponse)
async def get_project_tree(
    project_id: uuid.UUID,
    use_case: GetProjectTree = Depends(get_project_tree_factory),
) -> ProjectTreeResponse:
    tree = await use_case.execute(GetProjectTreeParams(project_id=project_id))
    return ProjectTreeResponse.model_validate(tree)
