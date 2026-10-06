import uuid

import pytest

from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.entities.objects.diagram_presence import DiagramPresence
from app.domain.services.presence_ledger import PresenceLedger

WORKSPACE = uuid.uuid4()
OTHER_WORKSPACE = uuid.uuid4()
PROJECT = uuid.uuid4()
OTHER_PROJECT = uuid.uuid4()
HERE = DiagramLocation(workspace_id=WORKSPACE, project_id=PROJECT)
ELSEWHERE = DiagramLocation(workspace_id=OTHER_WORKSPACE, project_id=OTHER_PROJECT)


@pytest.fixture
def sut() -> PresenceLedger[str]:
    return PresenceLedger[str]()


def presence(diagram_id: str, *entries: str, project: uuid.UUID = PROJECT) -> DiagramPresence[str]:
    return DiagramPresence(diagram_id, project, entries)


def test_should_start_one_batch_per_workspace_until_it_is_taken(sut: PresenceLedger[str]) -> None:
    assert sut.record("b", HERE, ["ana"], watched=True) is True
    assert sut.record("a", HERE, ["bruno"], watched=True) is False
    assert sut.record("c", ELSEWHERE, ["carla"], watched=True) is True

    sut.take_changes(WORKSPACE)

    assert sut.record("a", HERE, [], watched=True) is True


def test_should_take_the_changed_diagrams_in_order_once(sut: PresenceLedger[str]) -> None:
    sut.record("b", HERE, ["ana"], watched=True)
    sut.record("a", HERE, ["bruno", "carla"], watched=True)

    assert sut.take_changes(WORKSPACE) == [presence("a", "bruno", "carla"), presence("b", "ana")]
    assert sut.take_changes(WORKSPACE) == []


def test_should_keep_each_workspace_changes_to_itself(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana"], watched=True)
    sut.record("z", ELSEWHERE, ["zoe"], watched=True)

    assert sut.take_changes(WORKSPACE) == [presence("a", "ana")]
    assert sut.take_changes(OTHER_WORKSPACE) == [presence("z", "zoe", project=OTHER_PROJECT)]


def test_should_report_a_diagram_everyone_left_as_empty(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana"], watched=True)
    sut.take_changes(WORKSPACE)

    sut.record("a", HERE, [], watched=True)

    assert sut.take_changes(WORKSPACE) == [presence("a")]


def test_should_leave_out_a_reload_that_ends_as_it_started(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana", "bruno"], watched=True)
    sut.take_changes(WORKSPACE)

    sut.record("a", HERE, ["bruno"], watched=True)
    sut.record("a", HERE, ["ana", "bruno"], watched=True)

    assert sut.take_changes(WORKSPACE) == []


def test_should_leave_out_a_visit_nobody_was_told_about(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana"], watched=True)
    sut.record("a", HERE, [], watched=True)

    assert sut.take_changes(WORKSPACE) == []


def test_should_count_unwatched_changes_as_told(sut: PresenceLedger[str]) -> None:
    assert sut.record("a", HERE, ["ana"], watched=False) is False
    assert sut.take_changes(WORKSPACE) == []

    sut.record("a", HERE, ["ana"], watched=True)
    assert sut.take_changes(WORKSPACE) == []

    sut.record("b", HERE, ["bruno"], watched=False)
    sut.record("b", HERE, [], watched=True)
    assert sut.take_changes(WORKSPACE) == [presence("b")]


def test_should_report_the_latest_project_of_a_diagram(sut: PresenceLedger[str]) -> None:
    moved = DiagramLocation(workspace_id=WORKSPACE, project_id=OTHER_PROJECT)
    sut.record("a", HERE, ["ana"], watched=True)
    sut.record("a", moved, ["ana", "bruno"], watched=True)

    assert sut.take_changes(WORKSPACE) == [presence("a", "ana", "bruno", project=OTHER_PROJECT)]


def test_should_snapshot_the_workspace_diagrams_someone_is_in(sut: PresenceLedger[str]) -> None:
    sut.record("c", HERE, ["carla"], watched=False)
    sut.record("a", HERE, ["ana"], watched=True)
    sut.record("b", HERE, ["bruno"], watched=True)
    sut.record("b", HERE, [], watched=True)
    sut.record("z", ELSEWHERE, ["zoe"], watched=False)

    assert sut.snapshot(WORKSPACE) == [presence("a", "ana"), presence("c", "carla")]


def test_should_snapshot_nothing_once_everyone_left(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana"], watched=False)
    sut.record("a", HERE, [], watched=False)

    assert sut.snapshot(WORKSPACE) == []
    assert sut.snapshot(OTHER_WORKSPACE) == []

    sut.record("b", HERE, ["bruno"], watched=False)
    assert sut.snapshot(WORKSPACE) == [presence("b", "bruno")]


def test_should_keep_taking_changes_after_an_unchanged_diagram(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana"], watched=True)
    sut.take_changes(WORKSPACE)

    sut.record("a", HERE, [], watched=True)
    sut.record("a", HERE, ["ana"], watched=True)
    sut.record("b", HERE, ["bruno"], watched=True)

    assert sut.take_changes(WORKSPACE) == [presence("b", "bruno")]


def test_should_report_someone_back_in_a_diagram_they_had_left(sut: PresenceLedger[str]) -> None:
    sut.record("a", HERE, ["ana"], watched=True)
    sut.take_changes(WORKSPACE)
    sut.record("a", HERE, [], watched=True)
    sut.take_changes(WORKSPACE)

    sut.record("a", HERE, ["ana"], watched=True)

    assert sut.take_changes(WORKSPACE) == [presence("a", "ana")]


@pytest.mark.parametrize("watched", [True, False])
def test_should_accept_an_empty_diagram_it_never_saw(
    sut: PresenceLedger[str], watched: bool
) -> None:
    sut.record("a", HERE, [], watched=watched)

    assert sut.snapshot(WORKSPACE) == []
    assert sut.take_changes(WORKSPACE) == []
