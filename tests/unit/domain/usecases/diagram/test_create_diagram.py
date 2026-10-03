import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.usecases.diagram.create_diagram import CreateDiagram, CreateDiagramParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> CreateDiagram:
    return CreateDiagram(repo)


async def test_should_create_the_diagram_from_the_params(
    sut: CreateDiagram, repo: NonCallableMagicMock
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
    created = repo.create.await_args.args[0]
    assert result is created
    assert created.project_id == project_id
    assert created.name == "Flow"
    assert created.folder_id == folder_id
    assert created.canvas_state == canvas_state
