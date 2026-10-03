import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.revision_recorder import RevisionRecorder
from app.domain.usecases.diagram.update_diagram import UpdateDiagram, UpdateDiagramParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramRepository)


@pytest.fixture
def notifier() -> NonCallableMagicMock:
    return double(DiagramUpdateNotifier)


@pytest.fixture
def recorder() -> NonCallableMagicMock:
    return double(RevisionRecorder)


@pytest.fixture
def sut(
    repo: NonCallableMagicMock, notifier: NonCallableMagicMock, recorder: NonCallableMagicMock
) -> UpdateDiagram:
    return UpdateDiagram(repo, notifier, recorder)


def existing_diagram() -> Diagram:
    return Diagram(project_id=uuid.uuid4(), name="Old", canvas_state={"shapes": ["old"]})


async def test_should_replace_fields_and_return_persisted_diagram(
    sut: UpdateDiagram, repo: NonCallableMagicMock
) -> None:
    diagram = existing_diagram()
    folder_id = uuid.uuid4()
    repo.get_by_id.return_value = diagram
    repo.update.side_effect = lambda updated: updated
    result = await sut.execute(
        UpdateDiagramParams(
            diagram_id=diagram.id,
            name="New",
            folder_id=folder_id,
            canvas_state={"shapes": ["new"]},
            semantic_metadata={"shape:1": {"type": "service"}},
        )
    )
    repo.get_by_id.assert_awaited_once_with(diagram.id)
    assert result.folder_id == folder_id
    assert result.name == "New"
    assert result.canvas_state == {"shapes": ["new"]}
    assert result.semantic_metadata == {"shape:1": {"type": "service"}}


async def test_should_notify_open_editors_with_origin_client_id(
    sut: UpdateDiagram, repo: NonCallableMagicMock, notifier: NonCallableMagicMock
) -> None:
    diagram = existing_diagram()
    persisted = diagram.model_copy(update={"name": "New"})
    repo.get_by_id.return_value = diagram
    repo.update.return_value = persisted
    await sut.execute(
        UpdateDiagramParams(diagram_id=diagram.id, name="New", origin_client_id="tab-1")
    )
    notifier.notify_updated.assert_awaited_once_with(persisted, "tab-1")


async def test_should_notify_without_origin_when_writer_is_not_an_editor(
    sut: UpdateDiagram, repo: NonCallableMagicMock, notifier: NonCallableMagicMock
) -> None:
    diagram = existing_diagram()
    repo.get_by_id.return_value = diagram
    repo.update.return_value = diagram
    await sut.execute(UpdateDiagramParams(diagram_id=diagram.id, name="New"))
    notifier.notify_updated.assert_awaited_once_with(diagram, None)


async def test_should_raise_not_found_and_notify_nobody_when_diagram_missing(
    sut: UpdateDiagram, repo: NonCallableMagicMock, notifier: NonCallableMagicMock
) -> None:
    diagram_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=str(diagram_id)):
        await sut.execute(UpdateDiagramParams(diagram_id=diagram_id, name="New"))
    notifier.notify_updated.assert_not_awaited()


async def test_should_record_the_change_with_its_author_and_summary(
    sut: UpdateDiagram, repo: NonCallableMagicMock, recorder: NonCallableMagicMock
) -> None:
    diagram = existing_diagram()
    repo.get_by_id.return_value = diagram.model_copy()
    repo.update.side_effect = lambda updated: updated
    author = RevisionAuthor(origin=RevisionOrigin.AGENT, agent_name="Claude")
    await sut.execute(
        UpdateDiagramParams(
            diagram_id=diagram.id,
            name="New",
            canvas_state={"shapes": ["new"]},
            author=author,
            revision_summary="Renamed it",
        )
    )
    recorder.record.assert_awaited_once_with(
        diagram.id,
        DiagramSnapshot.of(diagram),
        DiagramSnapshot(name="New", canvas_state={"shapes": ["new"]}),
        author,
        summary="Renamed it",
    )


async def test_should_record_nothing_when_diagram_missing(
    sut: UpdateDiagram, repo: NonCallableMagicMock, recorder: NonCallableMagicMock
) -> None:
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await sut.execute(UpdateDiagramParams(diagram_id=uuid.uuid4(), name="New"))
    recorder.record.assert_not_awaited()
