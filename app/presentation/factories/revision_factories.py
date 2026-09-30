from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.settings import get_settings
from app.domain.entities.objects.revision_policy import RevisionPolicy
from app.domain.services.revision_recorder import RevisionRecorder
from app.domain.usecases.revision.get_diagram_revision import GetDiagramRevision
from app.domain.usecases.revision.list_diagram_revisions import ListDiagramRevisions
from app.domain.usecases.revision.restore_diagram_revision import RestoreDiagramRevision
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.repositories.diagram_revision_repository import (
    DiagramRevisionRepositoryImpl,
)
from app.infra.database.session import get_session
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_diagram_update_notifier import RealtimeDiagramUpdateNotifier


def build_revision_recorder(session: AsyncSession) -> RevisionRecorder:
    settings = get_settings()
    policy = RevisionPolicy(
        interval_minutes=settings.revision_interval_minutes,
        retention_days=settings.revision_retention_days,
        max_per_diagram=settings.revision_max_per_diagram,
    )
    return RevisionRecorder(DiagramRevisionRepositoryImpl(session), policy)


async def list_diagram_revisions_factory(
    session: AsyncSession = Depends(get_session),
) -> ListDiagramRevisions:
    return ListDiagramRevisions(DiagramRevisionRepositoryImpl(session))


async def get_diagram_revision_factory(
    session: AsyncSession = Depends(get_session),
) -> GetDiagramRevision:
    return GetDiagramRevision(DiagramRevisionRepositoryImpl(session))


async def restore_diagram_revision_factory(
    session: AsyncSession = Depends(get_session),
) -> RestoreDiagramRevision:
    return RestoreDiagramRevision(
        DiagramRepositoryImpl(session),
        DiagramRevisionRepositoryImpl(session),
        build_revision_recorder(session),
        RealtimeDiagramUpdateNotifier(manager),
    )
