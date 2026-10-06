import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.contracts.diagram_rooms import DiagramRooms
from app.domain.contracts.realtime_connection import RealtimeConnection
from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.objects.cursor_position import CursorPosition
from app.domain.entities.objects.diagram_location import DiagramLocation
from app.domain.entities.objects.participant import Participant
from app.infra.realtime.cursor_message import CursorMessage
from app.infra.realtime.presence_messages import (
    AgentEntry,
    PersonEntry,
    PresenceEntry,
    PresenceMessage,
)
from app.infra.realtime.room_presence_listener import RoomPresenceListener
from app.infra.realtime.workspace_presence_hub import workspace_presence_hub


@dataclass
class ActiveAgent:
    identity: AgentIdentity
    expiry: asyncio.Task[None]

    def presence_entry(self) -> AgentEntry:
        return AgentEntry(
            id=self.identity.id,
            name=self.identity.name,
            owner_id=str(self.identity.owner_id) if self.identity.owner_id else None,
            owner_name=self.identity.owner_name,
            label=self.identity.label,
        )

    def sort_key(self) -> tuple[str, str, str]:
        return (
            (self.identity.owner_name or "").lower(),
            self.identity.name.lower(),
            self.identity.id,
        )


class ConnectionManager(DiagramRooms):
    def __init__(self, listener: RoomPresenceListener) -> None:
        self._rooms: dict[str, dict[RealtimeConnection, Participant]] = {}
        # Agents (the MCP server) have no socket; each one's timer removes it when it goes quiet.
        self._agents: dict[str, dict[str, ActiveAgent]] = {}
        # Rooms of real diagrams, kept while someone (or an agent) is in them.
        self._locations: dict[str, DiagramLocation] = {}
        self._listener = listener

    async def connect(
        self,
        ws: RealtimeConnection,
        diagram_id: str,
        participant: Participant,
        location: DiagramLocation | None = None,
    ) -> None:
        await ws.accept()
        self._rooms.setdefault(diagram_id, {})[ws] = participant
        self._locate(diagram_id, location)
        self._room_changed(diagram_id)

    def disconnect(self, ws: RealtimeConnection, diagram_id: str) -> None:
        room = self._rooms.get(diagram_id, {})
        if room.pop(ws, None) is None:
            return
        if not room:
            self._rooms.pop(diagram_id, None)
        self._room_changed(diagram_id)

    def peer_count(self, diagram_id: str) -> int:
        return len(self.participants(diagram_id))

    # One entry per person: the same user in two tabs is shown once. Agents come last.
    def participants(self, diagram_id: str) -> list[PresenceEntry]:
        unique: dict[str, PersonEntry] = {}
        for participant in self._rooms.get(diagram_id, {}).values():
            unique.setdefault(
                participant.presence_id,
                PersonEntry(
                    id=participant.presence_id,
                    name=participant.name,
                    picture_url=participant.picture_url,
                ),
            )
        people: list[PresenceEntry] = sorted(unique.values(), key=lambda item: item.name.lower())
        agents = sorted(self._agents.get(diagram_id, {}).values(), key=ActiveAgent.sort_key)
        return people + [agent.presence_entry() for agent in agents]

    async def mark_agent_active(
        self,
        diagram_id: str,
        identity: AgentIdentity,
        seconds: float,
        location: DiagramLocation | None = None,
    ) -> None:
        agents = self._agents.setdefault(diagram_id, {})
        previous = agents.pop(identity.id, None)
        if previous is not None:
            previous.expiry.cancel()
        expiry = asyncio.create_task(self._expire_agent(diagram_id, identity.id, seconds))
        agents[identity.id] = ActiveAgent(identity=identity, expiry=expiry)
        self._locate(diagram_id, location)
        if previous is None or previous.identity != identity:
            self._room_changed(diagram_id)
            await self.broadcast_presence(diagram_id)

    async def _expire_agent(self, diagram_id: str, agent_id: str, seconds: float) -> None:
        await asyncio.sleep(seconds)
        agents = self._agents.get(diagram_id, {})
        agents.pop(agent_id, None)
        if not agents:
            self._agents.pop(diagram_id, None)
        self._room_changed(diagram_id)
        await self.broadcast_presence(diagram_id)

    async def broadcast(
        self, message: str, diagram_id: str, exclude: RealtimeConnection | None = None
    ) -> None:
        peers = [ws for ws in self._rooms.get(diagram_id, {}) if ws is not exclude]
        results = await asyncio.gather(
            *[ws.send_text(message) for ws in peers], return_exceptions=True
        )
        self._drop_failed(diagram_id, peers, results)

    async def relay_cursor(
        self, ws: RealtimeConnection, diagram_id: str, position: CursorPosition | None
    ) -> None:
        sender = self._rooms.get(diagram_id, {}).get(ws)
        if sender is None:
            return
        message = CursorMessage(
            id=sender.presence_id,
            name=sender.name,
            point=position.point if position else None,
            page=position.page_id if position else None,
        )
        await self.broadcast(message.model_dump_json(), diagram_id, exclude=ws)

    # Everyone gets the full list plus which entry is them, so clients can hide themselves.
    async def broadcast_presence(self, diagram_id: str) -> None:
        room = self._rooms.get(diagram_id, {})
        users = self.participants(diagram_id)
        peers = list(room)
        messages = [
            PresenceMessage(users=users, you=room[ws].presence_id, peers=len(users)) for ws in peers
        ]
        results = await asyncio.gather(
            *[
                ws.send_text(message.model_dump_json())
                for ws, message in zip(peers, messages, strict=True)
            ],
            return_exceptions=True,
        )
        if self._drop_failed(diagram_id, peers, results):
            await self.broadcast_presence(diagram_id)

    def _locate(self, diagram_id: str, location: DiagramLocation | None) -> None:
        if location is not None:
            self._locations[diagram_id] = location

    # Tells the workspace's sidebars, then forgets where an empty room was.
    def _room_changed(self, diagram_id: str) -> None:
        location = self._locations.get(diagram_id)
        if location is None:
            return
        self._listener.room_changed(diagram_id, location, self.participants(diagram_id))
        if diagram_id not in self._rooms and diagram_id not in self._agents:
            del self._locations[diagram_id]

    # A socket that can't be written to is gone (closed tab, sleeping laptop): stop counting it.
    def _drop_failed(
        self, diagram_id: str, peers: list[RealtimeConnection], results: Sequence[object]
    ) -> bool:
        failed = [
            ws for ws, result in zip(peers, results, strict=True) if isinstance(result, Exception)
        ]
        for ws in failed:
            self.disconnect(ws, diagram_id)
        return failed != []


manager = ConnectionManager(workspace_presence_hub)
