import uuid

from fastapi import APIRouter, Depends

from app.domain.usecases.diagram.create_diagram import CreateDiagram, CreateDiagramParams
from app.domain.usecases.diagram.delete_diagram import DeleteDiagram, DeleteDiagramParams
from app.domain.usecases.diagram.get_diagram import GetDiagram, GetDiagramParams
from app.domain.usecases.diagram.list_diagrams import ListDiagrams, ListDiagramsParams
from app.domain.usecases.diagram.update_diagram import UpdateDiagram, UpdateDiagramParams
from app.presentation.factories.diagram_factories import (
    create_diagram_factory,
    delete_diagram_factory,
    get_diagram_factory,
    list_diagrams_factory,
    update_diagram_factory,
)
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.diagram_schemas import (
    CreateDiagramRequest,
    DiagramResponse,
    UpdateDiagramRequest,
)

router = APIRouter(
    prefix="/projects/{project_id}/diagrams",
    tags=["diagrams"],
    dependencies=[Depends(require_workspace_access)],
)


@router.get("", response_model=list[DiagramResponse])
async def list_diagrams(
    project_id: uuid.UUID,
    use_case: ListDiagrams = Depends(list_diagrams_factory),
) -> list[DiagramResponse]:
    diagrams = await use_case.execute(ListDiagramsParams(project_id=project_id))
    return [DiagramResponse.model_validate(d) for d in diagrams]


@router.post("", response_model=DiagramResponse, status_code=201)
async def create_diagram(
    project_id: uuid.UUID,
    body: CreateDiagramRequest,
    use_case: CreateDiagram = Depends(create_diagram_factory),
) -> DiagramResponse:
    diagram = await use_case.execute(
        CreateDiagramParams(
            project_id=project_id,
            name=body.name,
            folder_id=body.folder_id,
            canvas_state=body.canvas_state,
        )
    )
    return DiagramResponse.model_validate(diagram)


@router.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    project_id: uuid.UUID,
    diagram_id: uuid.UUID,
    use_case: GetDiagram = Depends(get_diagram_factory),
) -> DiagramResponse:
    diagram = await use_case.execute(GetDiagramParams(diagram_id=diagram_id))
    return DiagramResponse.model_validate(diagram)


@router.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    project_id: uuid.UUID,
    diagram_id: uuid.UUID,
    body: UpdateDiagramRequest,
    use_case: UpdateDiagram = Depends(update_diagram_factory),
) -> DiagramResponse:
    diagram = await use_case.execute(
        UpdateDiagramParams(
            diagram_id=diagram_id,
            name=body.name,
            folder_id=body.folder_id,
            canvas_state=body.canvas_state,
            semantic_metadata=body.semantic_metadata,
        )
    )
    return DiagramResponse.model_validate(diagram)


@router.delete("/{diagram_id}", status_code=204)
async def delete_diagram(
    project_id: uuid.UUID,
    diagram_id: uuid.UUID,
    use_case: DeleteDiagram = Depends(delete_diagram_factory),
) -> None:
    await use_case.execute(DeleteDiagramParams(diagram_id=diagram_id))
