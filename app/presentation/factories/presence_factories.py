from app.domain.usecases.presence.track_agent_activity import TrackAgentActivity
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_agent_presence import RealtimeAgentPresence


async def track_agent_activity_factory() -> TrackAgentActivity:
    return TrackAgentActivity(RealtimeAgentPresence(manager))
