from app.domain.contracts.diagram_rooms import DiagramRooms
from app.domain.usecases.presence.track_agent_activity import TrackAgentActivity
from app.infra.realtime.connection_manager import manager
from app.infra.realtime.realtime_agent_presence import RealtimeAgentPresence


async def track_agent_activity_factory() -> TrackAgentActivity:
    return TrackAgentActivity(RealtimeAgentPresence(manager))


# One registry per process: every editor of a diagram must land in the same room.
def diagram_rooms_factory() -> DiagramRooms:
    return manager
