import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.project_placement import ProjectPlacement
from app.domain.usecases.diagram.create_diagram import CreateDiagram, CreateDiagramParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def placement() -> NonCallableMagicMock:
    return double(ProjectPlacement)


@pytest.fixture
def sut(repo: NonCallableMagicMock, placement: NonCallableMagicMock) -> CreateDiagram:
    return CreateDiagram(repo, placement)


async def test_should_create_the_diagram_from_the_params(
    sut: CreateDiagram, repo: NonCallableMagicMock, placement: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    folder_id = uuid.uuid4()
    canvas_state: dict[str, object] = {"records": []}
    repo.create.side_effect = lambda diagram: diagram
    result = await sut.execute(
        CreateDiagramParams(
            project_id=project_id, name="Flow", folder_id=folder_id, canvas_state=canvas_state
        )
    )
    placement.check_new.assert_awaited_once_with(project_id, folder_id)
    created = repo.create.await_args.args[0]
    assert result is created
    assert created.project_id == project_id
    assert created.name == "Flow"
    assert created.folder_id == folder_id
    assert created.canvas_state == canvas_state


async def test_should_not_create_the_diagram_when_its_place_is_missing(
    sut: CreateDiagram, repo: NonCallableMagicMock, placement: NonCallableMagicMock
) -> None:
    placement.check_new.side_effect = NotFoundError("Project not found")
    with pytest.raises(NotFoundError, match="Project not found"):
        await sut.execute(CreateDiagramParams(project_id=uuid.uuid4(), name="Flow"))
    repo.create.assert_not_awaited()
