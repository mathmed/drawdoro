import uuid
from datetime import UTC, datetime, timedelta, tzinfo
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.constants.revisions import SESSION_LOOKBACK
from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.objects.revision_policy import RevisionPolicy
from app.domain.enums.revision_kind import RevisionKind
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.services import revision_recorder
from app.domain.services.revision_recorder import RevisionRecorder
from tests.doubles import double

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
def repo() -> NonCallableMagicMock:
    mock = double(DiagramRevisionRepository)
    mock.create.side_effect = lambda created: created
    mock.update_snapshot.side_effect = lambda updated: updated
    return mock


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> RevisionRecorder:
    return RevisionRecorder(repo, RevisionPolicy(interval_minutes=10, retention_days=30))


def with_latest(repo: NonCallableMagicMock, latest: DiagramRevision | None) -> None:
    with_history(repo, [latest] if latest is not None else [])


def with_history(repo: NonCallableMagicMock, newest_first: list[DiagramRevision]) -> None:
    repo.get_latest.return_value = newest_first[0] if newest_first else None
    repo.list_by_diagram.return_value = newest_first


def created(repo: NonCallableMagicMock) -> list[DiagramRevision]:
    return [call.args[0] for call in repo.create.await_args_list]


async def test_should_coalesce_a_persons_saves_within_the_interval(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    latest = revision(1)
    with_latest(repo, latest)
    result = await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    assert result.id == latest.id
    assert result.snapshot == snapshot(2)
    assert result.updated_at > latest.updated_at
    repo.create.assert_not_awaited()


async def test_should_start_a_new_revision_after_the_interval(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, revision(1, age=timedelta(minutes=11)))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    [new] = created(repo)
    assert (new.kind, new.author_id, new.snapshot) == (RevisionKind.EDIT, ANA.user_id, snapshot(2))
    repo.update_snapshot.assert_not_awaited()


async def test_should_start_a_new_revision_when_someone_else_edits(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, revision(1, author=ANA))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), BRUNO)
    [new] = created(repo)
    assert new.author_id == BRUNO.user_id


async def test_should_give_every_agent_change_its_own_revision(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, revision(1, author=ANAS_AGENT))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANAS_AGENT, summary="Added a queue")
    [new] = created(repo)
    assert new.origin == RevisionOrigin.AGENT
    assert (new.author_id, new.agent_name, new.agent_label) == (ANA.user_id, "Claude", "laptop")
    assert new.summary == "Added a queue"


async def test_should_not_let_a_person_overwrite_an_agent_revision(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, revision(1, author=ANAS_AGENT))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    assert len(created(repo)) == 1
    repo.update_snapshot.assert_not_awaited()


async def test_should_capture_the_state_before_a_change_missing_from_the_history(
    sut: RevisionRecorder, repo: NonCallableMagicMock
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
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, revision(1, author=RevisionAuthor(), kind=RevisionKind.BASELINE))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), RevisionAuthor())
    assert len(created(repo)) == 1
    repo.update_snapshot.assert_not_awaited()


async def test_should_skip_the_baseline_of_an_empty_diagram(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    [edit] = created(repo)
    assert edit.kind == RevisionKind.EDIT


async def test_should_record_nothing_when_the_content_did_not_change(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    latest = revision(1, author=BRUNO)
    with_latest(repo, latest)
    assert await sut.record(DIAGRAM_ID, snapshot(1), snapshot(1), ANAS_AGENT) == latest
    repo.create.assert_not_awaited()
    repo.prune.assert_not_awaited()


async def test_should_record_restores_as_new_revisions(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    source = uuid.uuid4()
    with_latest(repo, revision(3))
    await sut.record(DIAGRAM_ID, snapshot(3), snapshot(1), ANA, restored_from_id=source)
    [restore] = created(repo)
    assert (restore.kind, restore.restored_from_id) == (RevisionKind.RESTORE, source)


async def test_should_prune_with_the_retention_policy(
    repo: NonCallableMagicMock,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=7, max_per_diagram=50))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    call = repo.prune.await_args
    assert call is not None
    diagram_id, keep_latest, older_than = call.args
    assert (diagram_id, keep_latest) == (DIAGRAM_ID, 50)
    expected = datetime.now(UTC) - timedelta(days=7)
    assert abs((older_than - expected).total_seconds()) < 5


async def test_should_not_prune_when_retention_is_disabled(
    repo: NonCallableMagicMock,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=0, max_per_diagram=0))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    repo.prune.assert_not_awaited()


async def test_should_keep_revisions_of_any_age_when_only_the_count_is_limited(
    repo: NonCallableMagicMock,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=0, max_per_diagram=10))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    repo.prune.assert_awaited_once_with(DIAGRAM_ID, 10, None)


async def test_should_keep_one_revision_per_person_when_editing_together(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    anas = revision(1, author=ANA, age=timedelta(minutes=3))
    with_history(repo, [revision(2, author=BRUNO), anas])
    result = await sut.record(DIAGRAM_ID, snapshot(2), snapshot(3), ANA)
    assert result.id == anas.id
    assert result.snapshot == snapshot(3)
    repo.create.assert_not_awaited()


async def test_should_not_reach_past_an_agent_change_for_a_session(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_history(repo, [revision(2, author=ANAS_AGENT), revision(1, author=ANA)])
    await sut.record(DIAGRAM_ID, snapshot(2), snapshot(3), ANA)
    [new] = created(repo)
    assert (new.author_id, new.snapshot) == (ANA.user_id, snapshot(3))
    repo.update_snapshot.assert_not_awaited()


async def test_should_treat_empty_metadata_like_none(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    latest = revision(1, author=ANAS_AGENT)
    with_latest(repo, latest)
    editor_save = DiagramSnapshot(
        name="Checkout", canvas_state={"version": 1}, semantic_metadata={}
    )
    assert await sut.record(DIAGRAM_ID, snapshot(1), editor_save, ANA) == latest
    repo.create.assert_not_awaited()


NOW = datetime(2026, 10, 3, 12, 0, tzinfo=UTC)


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> FrozenDatetime:
        return cls.fromtimestamp(NOW.timestamp(), tz)


async def test_should_look_up_the_history_of_the_recorded_diagram(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    with_latest(repo, revision(1))
    await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    repo.get_latest.assert_awaited_once_with(DIAGRAM_ID)
    repo.list_by_diagram.assert_awaited_once_with(DIAGRAM_ID, SESSION_LOOKBACK)


async def test_should_still_coalesce_a_save_made_exactly_at_the_end_of_the_interval(
    sut: RevisionRecorder, repo: NonCallableMagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(revision_recorder, "datetime", FrozenDatetime)
    latest = revision(1).model_copy(update={"created_at": NOW - timedelta(minutes=10)})
    with_latest(repo, latest)
    result = await sut.record(DIAGRAM_ID, snapshot(1), snapshot(2), ANA)
    assert result.id == latest.id
    repo.create.assert_not_awaited()


async def test_should_prune_revisions_older_than_a_single_retention_day(
    repo: NonCallableMagicMock,
) -> None:
    sut = RevisionRecorder(repo, RevisionPolicy(retention_days=1, max_per_diagram=0))
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), ANA)
    call = repo.prune.await_args
    assert call is not None
    diagram_id, keep_latest, older_than = call.args
    assert (diagram_id, keep_latest) == (DIAGRAM_ID, None)
    expected = datetime.now(UTC) - timedelta(days=1)
    assert abs((older_than - expected).total_seconds()) < 5


async def test_should_sign_a_new_revision_with_the_authors_name_and_picture(
    sut: RevisionRecorder, repo: NonCallableMagicMock
) -> None:
    author = RevisionAuthor(user_id=uuid.uuid4(), name="Ana", picture_url="https://x/ana.png")
    with_latest(repo, None)
    await sut.record(DIAGRAM_ID, DiagramSnapshot(name="New"), snapshot(1), author)
    [new] = created(repo)
    assert (new.author_name, new.author_picture_url) == ("Ana", "https://x/ana.png")
