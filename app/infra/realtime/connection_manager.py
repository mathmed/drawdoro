import asyncio
import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from app.domain.contracts.diagram_rooms import DiagramRooms
from app.domain.contracts.realtime_connection import RealtimeConnection
from app.domain.entities.models.agent_identity import AgentIdentity
from app.domain.entities.objects.participant import Participant


class PresenceKind(StrEnum):
    PERSON = "person"
    AGENT = "agent"


@dataclass
class ActiveAgent:
    identity: AgentIdentity
    expiry: asyncio.Task[None]

    def presence_entry(self) -> dict[str, str | None]:
        entry: dict[str, str | None] = {
            "id": self.identity.id,
            "name": self.identity.name,
            "kind": PresenceKind.AGENT,
        }
        owner = {
            "owner_id": str(self.identity.owner_id) if self.identity.owner_id else None,
            "owner_name": self.identity.owner_name,
            "label": self.identity.label,
        }
        return entry | {key: value for key, value in owner.items() if value is not None}

    def sort_key(self) -> tuple[str, str, str]:
        return (
            (self.identity.owner_name or "").lower(),
            self.identity.name.lower(),
            self.identity.id,
        )


class ConnectionManager(DiagramRooms):
    def __init__(self) -> None:
        self._rooms: dict[str, dict[RealtimeConnection, Participant]] = {}
        # Agents (the MCP server) have no socket; each one's timer removes it when it goes quiet.
        self._agents: dict[str, dict[str, ActiveAgent]] = {}

    async def connect(
        self, ws: RealtimeConnection, diagram_id: str, participant: Participant
    ) -> None:
        await ws.accept()
        self._rooms.setdefault(diagram_id, {})[ws] = participant

    def disconnect(self, ws: RealtimeConnection, diagram_id: str) -> None:
        room = self._rooms.get(diagram_id, {})
        room.pop(ws, None)
        if not room:
            self._rooms.pop(diagram_id, None)

    def peer_count(self, diagram_id: str) -> int:
        return len(self.participants(diagram_id))

    # One entry per person: the same user in two tabs is shown once. Agents come last.
    def participants(self, diagram_id: str) -> list[dict[str, str | None]]:
        unique: dict[str, dict[str, str | None]] = {}
        for participant in self._rooms.get(diagram_id, {}).values():
            unique.setdefault(
                participant.presence_id,
                {
                    "id": participant.presence_id,
                    "name": participant.name,
                    "kind": PresenceKind.PERSON,
                    "picture_url": participant.picture_url,
                },
            )
        people = sorted(unique.values(), key=lambda item: str(item["name"]).lower())
        agents = sorted(self._agents.get(diagram_id, {}).values(), key=ActiveAgent.sort_key)
        return people + [agent.presence_entry() for agent in agents]

    async def mark_agent_active(
        self, diagram_id: str, identity: AgentIdentity, seconds: float
    ) -> None:
        agents = self._agents.setdefault(diagram_id, {})
        previous = agents.pop(identity.id, None)
        if previous is not None:
            previous.expiry.cancel()
        expiry = asyncio.create_task(self._expire_agent(diagram_id, identity.id, seconds))
        agents[identity.id] = ActiveAgent(identity=identity, expiry=expiry)
        if previous is None or previous.identity != identity:
            await self.broadcast_presence(diagram_id)

    async def _expire_agent(self, diagram_id: str, agent_id: str, seconds: float) -> None:
        await asyncio.sleep(seconds)
        agents = self._agents.get(diagram_id, {})
        agents.pop(agent_id, None)
        if not agents:
            self._agents.pop(diagram_id, None)
        await self.broadcast_presence(diagram_id)

    async def broadcast(
        self, message: str, diagram_id: str, exclude: RealtimeConnection | None = None
    ) -> None:
        peers = [ws for ws in self._rooms.get(diagram_id, {}) if ws is not exclude]
        results = await asyncio.gather(
            *[ws.send_text(message) for ws in peers], return_exceptions=True
        )
        self._drop_failed(diagram_id, peers, results)

    # Everyone gets the full list plus which entry is them, so clients can hide themselves.
    async def broadcast_presence(self, diagram_id: str) -> None:
        room = self._rooms.get(diagram_id, {})
        users = self.participants(diagram_id)
        peers = list(room)
        messages = [
            json.dumps(
                {
                    "type": "presence",
                    "users": users,
                    "you": room[ws].presence_id,
                    "peers": len(users),
                }
            )
            for ws in peers
        ]
        results = await asyncio.gather(
            *[ws.send_text(message) for ws, message in zip(peers, messages, strict=True)],
            return_exceptions=True,
        )
        if self._drop_failed(diagram_id, peers, results):
            await self.broadcast_presence(diagram_id)

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


manager = ConnectionManager()
