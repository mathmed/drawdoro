import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.revision_recorder import RevisionRecorder
from app.domain.usecases.revision.restore_diagram_revision import (
    RestoreDiagramRevision,
    RestoreDiagramRevisionParams,
)
from tests.doubles import double

ANA = RevisionAuthor(user_id=uuid.uuid4(), name="Ana")


def current_diagram() -> Diagram:
    return Diagram(project_id=uuid.uuid4(), name="Checkout v3", canvas_state={"shapes": ["new"]})


def old_revision(diagram: Diagram) -> DiagramRevision:
    return DiagramRevision(
        diagram_id=diagram.id,
        snapshot=DiagramSnapshot(
            name="Checkout", canvas_state={"shapes": ["old"]}, semantic_metadata={"a": {}}
        ),
    )


@pytest.fixture
def diagrams() -> NonCallableMagicMock:
    mock = double(DiagramRepository)
    mock.update.side_effect = lambda updated: updated
    return mock


@pytest.fixture
def revisions() -> NonCallableMagicMock:
    return double(DiagramRevisionRepository)


@pytest.fixture
def recorder() -> NonCallableMagicMock:
    return double(RevisionRecorder)


@pytest.fixture
def notifier() -> NonCallableMagicMock:
    return double(DiagramUpdateNotifier)


@pytest.fixture
def sut(
    diagrams: NonCallableMagicMock,
    revisions: NonCallableMagicMock,
    recorder: NonCallableMagicMock,
    notifier: NonCallableMagicMock,
) -> RestoreDiagramRevision:
    return RestoreDiagramRevision(diagrams, revisions, recorder, notifier)


async def test_should_bring_back_the_canvas_and_record_a_restore(
    sut: RestoreDiagramRevision,
    diagrams: NonCallableMagicMock,
    revisions: NonCallableMagicMock,
    recorder: NonCallableMagicMock,
    notifier: NonCallableMagicMock,
) -> None:
    diagram = current_diagram()
    before = DiagramSnapshot.of(diagram)
    revision = old_revision(diagram)
    diagrams.get_by_id.return_value = diagram
    revisions.get.return_value = revision
    restored = await sut.execute(
        RestoreDiagramRevisionParams(diagram_id=diagram.id, revision_id=revision.id, author=ANA)
    )
    assert restored.name == "Checkout v3"
    assert restored.canvas_state == {"shapes": ["old"]}
    assert restored.semantic_metadata == {"a": {}}
    recorder.record.assert_awaited_once_with(
        diagram.id,
        before,
        DiagramSnapshot.of(restored),
        ANA,
        restored_from_id=revision.id,
    )
    notifier.notify_updated.assert_awaited_once_with(restored, None)
    diagrams.get_by_id.assert_awaited_once_with(diagram.id)
    revisions.get.assert_awaited_once_with(diagram.id, revision.id)


async def test_should_raise_not_found_for_missing_diagram(
    sut: RestoreDiagramRevision, diagrams: NonCallableMagicMock, notifier: NonCallableMagicMock
) -> None:
    diagrams.get_by_id.return_value = None
    diagram_id = uuid.uuid4()
    with pytest.raises(NotFoundError, match=f"^Diagram {diagram_id} not found$"):
        await sut.execute(
            RestoreDiagramRevisionParams(diagram_id=diagram_id, revision_id=uuid.uuid4())
        )
    notifier.notify_updated.assert_not_awaited()


async def test_should_raise_not_found_for_missing_revision(
    sut: RestoreDiagramRevision,
    diagrams: NonCallableMagicMock,
    revisions: NonCallableMagicMock,
) -> None:
    diagram = current_diagram()
    diagrams.get_by_id.return_value = diagram
    revisions.get.return_value = None
    revision_id = uuid.uuid4()
    with pytest.raises(NotFoundError, match=f"^Revision {revision_id} not found$"):
        await sut.execute(
            RestoreDiagramRevisionParams(diagram_id=diagram.id, revision_id=revision_id)
        )
    diagrams.update.assert_not_awaited()
