import uuid
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.objects.revision_policy import RevisionPolicy
from app.domain.enums.revision_kind import RevisionKind
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.services.revision_recorder import RevisionRecorder

DIAGRAM_ID = uuid.uuid4()
ANA = RevisionAuthor(user_id=uuid.uuid4())
BRUNO = RevisionAuthor(user_id=uuid.uuid4())
ANAS_AGENT = RevisionAuthor(
    user_id=ANA.user_id, origin=RevisionOrigin.AGENT, agent_name="Claude", agent_label="laptop"
)


def snapshot(version: int) -> DiagramSnapshot:
    return DiagramSnapshot(name="Checkout", canvas_state={"version": version})


def revision(
    version: int,
    author: RevisionAuthor = ANA,
    kind: RevisionKind = RevisionKind.EDIT,
    age: timedelta = timedelta(minutes=1),
) -> DiagramRevision:
    created = datetime.now(UTC) - age
    return DiagramRevision(
        diagram_id=DIAGRAM_ID,
        kind=kind,
        origin=author.origin,
        author_id=author.user_id,
        snapshot=snapshot(version),
        created_at=created,
        updated_at=created,
    )


@pytest.fixture
def repo() -> DiagramRevisionRepository:
    mock = cast(DiagramRevisionRepository, create_autospec(DiagramRevisionRepository))
    mock.create = AsyncMock(side_effect=lambda created: created)  # type: ignore[method-assign]
    mock.update_snapshot = AsyncMock(side_effect=lambda updated: updated)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def sut(repo: DiagramRevisionRepository) -> RevisionRecorder:
    return RevisionRecorder(repo, RevisionPolicy(interval_minutes=10, retention_days=30))


def with_latest(repo: DiagramRevisionRepository, latest: DiagramRevision | None) -> None:
    with_history(repo, [latest] if latest is not None else [])


def with_history(repo: DiagramRevisionRepository, newest_first: list[DiagramRevision]) -> None:
    repo.get_latest = AsyncMock(return_value=newest_first[0] if newest_first else None)  # type: ignore[method-assign]
    repo.list_by_diagram = AsyncMock(return_value=newest_first)  # type: ignore[method-assign]


def created(repo: DiagramRevisionRepository) -> list[DiagramRevision]:
    return [call.args[0] for call in cast(AsyncMock, repo.create).await_args_list]


async def test_should_coalesce_a_persons_saves_within_the_interval(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    latest = revision(1)
    with_latest(repo, latest)
    result = await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    assert result.id == latest.id
    assert result.snapshot == snapshot(2)
    assert result.updated_at > latest.updated_at
    cast(AsyncMock, repo.create).assert_not_awaited()


async def test_should_start_a_new_revision_after_the_interval(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, revision(1, age=timedelta(minutes=11)))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    [new] = created(repo)
    assert (new.kind, new.author_id, new.snapshot) == (RevisionKind.EDIT, ANA.user_id, snapshot(2))
    cast(AsyncMock, repo.update_snapshot).assert_not_awaited()


async def test_should_start_a_new_revision_when_someone_else_edits(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, revision(1, author=ANA))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), BRUNO)
    [new] = created(repo)
    assert new.author_id == BRUNO.user_id


async def test_should_give_every_agent_change_its_own_revision(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, revision(1, author=ANAS_AGENT))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANAS_AGENT, summary="Added a queue")
    [new] = created(repo)
    assert new.origin == RevisionOrigin.AGENT
    assert (new.author_id, new.agent_name, new.agent_label) == (ANA.user_id, "Claude", "laptop")
    assert new.summary == "Added a queue"


async def test_should_not_let_a_person_overwrite_an_agent_revision(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, revision(1, author=ANAS_AGENT))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    assert len(created(repo)) == 1
    cast(AsyncMock, repo.update_snapshot).assert_not_awaited()


async def test_should_capture_the_state_before_a_change_missing_from_the_history(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANAS_AGENT)
    baseline, edit = created(repo)
    assert (baseline.kind, baseline.author_id, baseline.snapshot) == (
        RevisionKind.BASELINE,
        None,
        snapshot(1),
    )
    assert (edit.kind, edit.snapshot) == (RevisionKind.EDIT, snapshot(2))


async def test_should_never_coalesce_into_a_baseline(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, revision(1, author=RevisionAuthor(), kind=RevisionKind.BASELINE))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), RevisionAuthor())
    assert len(created(repo)) == 1
    cast(AsyncMock, repo.update_snapshot).assert_not_awaited()


async def test_should_skip_the_baseline_of_an_empty_diagram(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    [edit] = created(repo)
    assert edit.kind == RevisionKind.EDIT


async def test_should_record_nothing_when_the_content_did_not_change(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    latest = revision(1, author=BRUNO)
    with_latest(repo, latest)
    assert await sut.record(DIAGRAM_ID, snapshot(1), snapshot(1), ANAS_AGENT) == latest
    cast(AsyncMock, repo.create).assert_not_awaited()
    cast(AsyncMock, repo.prune).assert_not_awaited()


async def test_should_record_restores_as_new_revisions(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    source = uuid.uuid4()
    with_latest(repo, revision(3))
    await sut.record(DIAGRAM_ID, snapshot(3), snapshot(1), ANA, restored_from_id=source)
    [restore] = created(repo)
    assert (restore.kind, restore.restored_from_id) == (RevisionKind.RESTORE, source)


async def test_should_prune_with_the_retention_policy(
    repo: DiagramRevisionRepository,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=7, max_per_diagram=50))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    call = cast(AsyncMock, repo.prune).await_args
    assert call is not None
    diagram_id, keep_latest, older_than = call.args
    assert (diagram_id, keep_latest) == (DIAGRAM_ID, 50)
    expected = datetime.now(UTC) - timedelta(days=7)
    assert abs((older_than - expected).total_seconds()) < 5


async def test_should_not_prune_when_retention_is_disabled(
    repo: DiagramRevisionRepository,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=0, max_per_diagram=0))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    cast(AsyncMock, repo.prune).assert_not_awaited()


async def test_should_keep_revisions_of_any_age_when_only_the_count_is_limited(
    repo: DiagramRevisionRepository,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=0, max_per_diagram=10))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    cast(AsyncMock, repo.prune).assert_awaited_once_with(DIAGRAM_ID, 10, None)


async def test_should_keep_one_revision_per_person_when_editing_together(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    anas = revision(1, author=ANA, age=timedelta(minutes=3))
    with_history(repo, [revision(2, author=BRUNO), anas])
    result = await sut.record(DIAGRAM_ID, snapshot(2), snapshot(3), ANA)
    assert result.id == anas.id
    assert result.snapshot == snapshot(3)
    cast(AsyncMock, repo.create).assert_not_awaited()


async def test_should_not_reach_past_an_agent_change_for_a_session(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    with_history(repo, [revision(2, author=ANAS_AGENT), revision(1, author=ANA)])
    await sut.record(DIAGRAM_ID, snapshot(2), snapshot(3), ANA)
    [new] = created(repo)
    assert (new.author_id, new.snapshot) == (ANA.user_id, snapshot(3))
    cast(AsyncMock, repo.update_snapshot).assert_not_awaited()


async def test_should_treat_empty_metadata_like_none(
    sut: RevisionRecorder, repo: DiagramRevisionRepository
) -> None:
    latest = revision(1, author=ANAS_AGENT)
    with_latest(repo, latest)
    editor_save = DiagramSnapshot(
        name="Checkout", canvas_state={"version": 1}, semantic_metadata={}
    )
    assert await sut.record(DIAGRAM_ID, snapshot(1), editor_save, ANA) == latest
    cast(AsyncMock, repo.create).assert_not_awaited()
