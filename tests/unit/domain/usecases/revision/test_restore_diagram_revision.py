import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

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
def diagrams() -> DiagramRepository:
    mock = cast(DiagramRepository, create_autospec(DiagramRepository))
    mock.update = AsyncMock(side_effect=lambda updated: updated)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def revisions() -> DiagramRevisionRepository:
    return cast(DiagramRevisionRepository, create_autospec(DiagramRevisionRepository))


@pytest.fixture
def recorder() -> RevisionRecorder:
    return cast(RevisionRecorder, create_autospec(RevisionRecorder, instance=True))


@pytest.fixture
def notifier() -> DiagramUpdateNotifier:
    return cast(DiagramUpdateNotifier, create_autospec(DiagramUpdateNotifier))


@pytest.fixture
def sut(
    diagrams: DiagramRepository,
    revisions: DiagramRevisionRepository,
    recorder: RevisionRecorder,
    notifier: DiagramUpdateNotifier,
) -> RestoreDiagramRevision:
    return RestoreDiagramRevision(diagrams, revisions, recorder, notifier)


async def test_should_bring_back_the_canvas_and_record_a_restore(
    sut: RestoreDiagramRevision,
    diagrams: DiagramRepository,
    revisions: DiagramRevisionRepository,
    recorder: RevisionRecorder,
    notifier: DiagramUpdateNotifier,
) -> None:
    diagram = current_diagram()
    before = DiagramSnapshot.of(diagram)
    revision = old_revision(diagram)
    diagrams.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    revisions.get = AsyncMock(return_value=revision)  # type: ignore[method-assign]
    restored = await sut.execute(
        RestoreDiagramRevisionParams(diagram_id=diagram.id, revision_id=revision.id, author=ANA)
    )
    assert restored.name == "Checkout v3"
    assert restored.canvas_state == {"shapes": ["old"]}
    assert restored.semantic_metadata == {"a": {}}
    cast(AsyncMock, recorder.record).assert_awaited_once_with(
        diagram.id,
        before,
        DiagramSnapshot.of(restored),
        ANA,
        restored_from_id=revision.id,
    )
    cast(AsyncMock, notifier.notify_updated).assert_awaited_once_with(restored, None)


async def test_should_raise_not_found_for_missing_diagram(
    sut: RestoreDiagramRevision, diagrams: DiagramRepository, notifier: DiagramUpdateNotifier
) -> None:
    diagrams.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        await sut.execute(
            RestoreDiagramRevisionParams(diagram_id=uuid.uuid4(), revision_id=uuid.uuid4())
        )
    cast(AsyncMock, notifier.notify_updated).assert_not_awaited()


async def test_should_raise_not_found_for_missing_revision(
    sut: RestoreDiagramRevision,
    diagrams: DiagramRepository,
    revisions: DiagramRevisionRepository,
) -> None:
    diagram = current_diagram()
    diagrams.get_by_id = AsyncMock(return_value=diagram)  # type: ignore[method-assign]
    revisions.get = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        await sut.execute(
            RestoreDiagramRevisionParams(diagram_id=diagram.id, revision_id=uuid.uuid4())
        )
    cast(AsyncMock, diagrams.update).assert_not_awaited()
