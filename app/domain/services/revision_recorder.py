import uuid
from datetime import UTC, datetime, timedelta

from app.domain.constants.revisions import SESSION_LOOKBACK
from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.entities.models.diagram_revision import DiagramRevision
from app.domain.entities.models.diagram_snapshot import DiagramSnapshot
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.entities.objects.revision_policy import RevisionPolicy
from app.domain.enums.revision_kind import RevisionKind
from app.domain.enums.revision_origin import RevisionOrigin


# Keeps the history of a diagram small but useful:
# - a person's saves (the editor autosaves every few seconds) coalesce into one revision per
#   interval, which always holds the latest state of that editing session;
# - every agent change and every restore gets a revision of its own, and the state before it is
#   captured first when the history doesn't already end with it;
# - after each write, revisions beyond the retention policy are deleted.
class RevisionRecorder:
    def __init__(self, repo: DiagramRevisionRepository, policy: RevisionPolicy) -> None:
        self._repo = repo
        self._policy = policy

    async def record(
        self,
        diagram_id: uuid.UUID,
        before: DiagramSnapshot,
        after: DiagramSnapshot,
        author: RevisionAuthor,
        summary: str | None = None,
        restored_from_id: uuid.UUID | None = None,
    ) -> DiagramRevision:
        latest = await self._repo.get_latest(diagram_id)
        if latest is not None and latest.snapshot == after:
            return latest
        await self._capture_baseline(diagram_id, latest, before)
        ongoing = None if restored_from_id else await self._ongoing_session(diagram_id, author)
        if ongoing is not None:
            revision = await self._repo.update_snapshot(
                ongoing.model_copy(update={"snapshot": after, "updated_at": datetime.now(UTC)})
            )
        else:
            revision = await self._repo.create(
                _new_revision(diagram_id, after, author, summary, restored_from_id)
            )
        await self._prune(diagram_id)
        return revision

    async def _capture_baseline(
        self, diagram_id: uuid.UUID, latest: DiagramRevision | None, before: DiagramSnapshot
    ) -> None:
        if before.is_empty or (latest is not None and latest.snapshot == before):
            return
        await self._repo.create(
            DiagramRevision(diagram_id=diagram_id, kind=RevisionKind.BASELINE, snapshot=before)
        )

    # This person's revision still within the interval. Other people's saves in between are skipped,
    # so people editing together get one revision each instead of one per autosave; an agent change,
    # restore or baseline in between ends the session, so the state it captured is never replaced.
    async def _ongoing_session(
        self, diagram_id: uuid.UUID, author: RevisionAuthor
    ) -> DiagramRevision | None:
        if author.origin != RevisionOrigin.HUMAN:
            return None
        recent = await self._repo.list_by_diagram(diagram_id, SESSION_LOOKBACK)
        mine = _latest_human_edit_by(recent, author)
        window_start = datetime.now(UTC) - timedelta(minutes=self._policy.interval_minutes)
        if mine is None or mine.created_at < window_start:
            return None
        return mine

    async def _prune(self, diagram_id: uuid.UUID) -> None:
        keep_latest = self._policy.max_per_diagram or None
        older_than = (
            datetime.now(UTC) - timedelta(days=self._policy.retention_days)
            if self._policy.retention_days > 0
            else None
        )
        if keep_latest is None and older_than is None:
            return
        await self._repo.prune(diagram_id, keep_latest, older_than)


def _latest_human_edit_by(
    newest_first: list[DiagramRevision], author: RevisionAuthor
) -> DiagramRevision | None:
    for revision in newest_first:
        if revision.kind != RevisionKind.EDIT or revision.origin != RevisionOrigin.HUMAN:
            return None
        if revision.author_id == author.user_id:
            return revision
    return None


def _new_revision(
    diagram_id: uuid.UUID,
    snapshot: DiagramSnapshot,
    author: RevisionAuthor,
    summary: str | None,
    restored_from_id: uuid.UUID | None,
) -> DiagramRevision:
    return DiagramRevision(
        diagram_id=diagram_id,
        kind=RevisionKind.RESTORE if restored_from_id else RevisionKind.EDIT,
        origin=author.origin,
        author_id=author.user_id,
        author_name=author.name,
        author_picture_url=author.picture_url,
        agent_name=author.agent_name,
        agent_label=author.agent_label,
        summary=summary,
        restored_from_id=restored_from_id,
        snapshot=snapshot,
    )
