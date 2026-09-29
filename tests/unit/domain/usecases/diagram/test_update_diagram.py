import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.entities.models.diagram import Diagram
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.update_diagram import UpdateDiagram, UpdateDiagramParams


@pytest.fixture
def repo() -> DiagramRepository:
    return cast(DiagramRepository, create_autospec(DiagramRepository))


@pytest.fixture
def notifier() -> DiagramUpdateNotifier:
    return cast(DiagramUpdateNotifier, create_autospec(DiagramUpdateNotifier))


@pytest.fixture
def sut(repo: DiagramRepository, notifier: DiagramUpdateNotifier) -> UpdateDiagram:
    return UpdateDiagram(repo, notifier)


def existing_diagram() -> Diagram:
    return Diagram(project_id=uuid.uuid4(), name="Old", canvas_state={"shapes": ["old"]})


async def test_should_replace_fields_and_return_persisted_diagram(
    sut: UpdateDiagram, repo: DiagramRepository
) -> None:
    diagram = existing_diagram()
    repo.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    repo.update = AsyncMock(side_effect=lambda updated: updated)  # type: ignore[method-assign]
    result = await sut.execute(
        UpdateDiagramParams(
            diagram_id=diagram.id,
            name="New",
            canvas_state={"shapes": ["new"]},
            semantic_metadata={"shape:1": {"type": "service"}},
        )
    )
    assert result.name == "New"
    assert result.canvas_state == {"shapes": ["new"]}
    assert result.semantic_metadata == {"shape:1": {"type": "service"}}


async def test_should_notify_open_editors_with_origin_client_id(
    sut: UpdateDiagram, repo: DiagramRepository, notifier: DiagramUpdateNotifier
) -> None:
    diagram = existing_diagram()
    persisted = diagram.model_copy(update={"name": "New"})
    repo.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    repo.update = AsyncMock(return_value=persisted)  # type: ignore[method-assign]
    await sut.execute(
        UpdateDiagramParams(diagram_id=diagram.id, name="New", origin_client_id="tab-1")
    )
    cast(AsyncMock, notifier.notify_updated).assert_awaited_once_with(persisted, "tab-1")


async def test_should_notify_without_origin_when_writer_is_not_an_editor(
    sut: UpdateDiagram, repo: DiagramRepository, notifier: DiagramUpdateNotifier
) -> None:
    diagram = existing_diagram()
    repo.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    repo.update = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    await sut.execute(UpdateDiagramParams(diagram_id=diagram.id, name="New"))
    cast(AsyncMock, notifier.notify_updated).assert_awaited_once_with(diagram, None)


async def test_should_raise_not_found_and_notify_nobody_when_diagram_missing(
    sut: UpdateDiagram, repo: DiagramRepository, notifier: DiagramUpdateNotifier
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError, match=str(diagram_id)):
        await sut.execute(UpdateDiagramParams(diagram_id=diagram_id, name="New"))
    cast(AsyncMock, notifier.notify_updated).assert_not_awaited()
