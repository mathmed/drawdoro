import asyncio
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from fastapi import WebSocket


class PresenceKind(StrEnum):
    PERSON = "person"
    AGENT = "agent"


@dataclass(frozen=True)
class Participant:
    name: str
    # None for guests (authentication disabled); they are told apart per connection.
    user_id: str | None = None
    connection_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def presence_id(self) -> str:
        return self.user_id or self.connection_id


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[WebSocket, Participant]] = {}
        # Agents (the MCP server) have no socket; each one's timer removes it when it goes quiet.
        self._agents: dict[str, dict[str, asyncio.Task[None]]] = {}

    async def connect(self, ws: WebSocket, diagram_id: str, participant: Participant) -> None:
        await ws.accept()
        self._rooms.setdefault(diagram_id, {})[ws] = participant

    def disconnect(self, ws: WebSocket, diagram_id: str) -> None:
        room = self._rooms.get(diagram_id, {})
        room.pop(ws, None)
        if not room:
            self._rooms.pop(diagram_id, None)

    def peer_count(self, diagram_id: str) -> int:
        return len(self.participants(diagram_id))

    # One entry per person: the same user in two tabs is shown once. Agents come last.
    def participants(self, diagram_id: str) -> list[dict[str, str]]:
        unique: dict[str, dict[str, str]] = {}
        for participant in self._rooms.get(diagram_id, {}).values():
            unique.setdefault(
                participant.presence_id,
                {
                    "id": participant.presence_id,
                    "name": participant.name,
                    "kind": PresenceKind.PERSON,
                },
            )
        people = sorted(unique.values(), key=lambda item: item["name"].lower())
        agents = [
            {"id": f"agent:{name}", "name": name, "kind": PresenceKind.AGENT}
            for name in sorted(self._agents.get(diagram_id, {}))
        ]
        return people + agents

    async def mark_agent_active(self, diagram_id: str, name: str, seconds: float) -> None:
        agents = self._agents.setdefault(diagram_id, {})
        previous = agents.pop(name, None)
        if previous is not None:
            previous.cancel()
        agents[name] = asyncio.create_task(self._expire_agent(diagram_id, name, seconds))
        if previous is None:
            await self.broadcast_presence(diagram_id)

    async def _expire_agent(self, diagram_id: str, name: str, seconds: float) -> None:
        await asyncio.sleep(seconds)
        agents = self._agents.get(diagram_id, {})
        agents.pop(name, None)
        if not agents:
            self._agents.pop(diagram_id, None)
        await self.broadcast_presence(diagram_id)

    async def broadcast(
        self, message: str, diagram_id: str, exclude: WebSocket | None = None
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
        self, diagram_id: str, peers: list[WebSocket], results: Sequence[object]
    ) -> bool:
        failed = [
            ws for ws, result in zip(peers, results, strict=True) if isinstance(result, Exception)
        ]
        for ws in failed:
            self.disconnect(ws, diagram_id)
        return failed != []


manager = ConnectionManager()
