import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class Transport(StrEnum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


@dataclass(frozen=True)
class Settings:
    api_url: str = "http://localhost:8000"
    api_key: str = ""
    # Shown to people with the diagram open while the agent works on it; empty hides it.
    agent_name: str = "Claude"
    transport: Transport = Transport.STDIO
    host: str = "127.0.0.1"
    port: int = 8001
    # Public hostnames accepted over HTTP besides localhost, e.g. the one routed by the ingress.
    allowed_hosts: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> Self:
        defaults = cls()
        return cls(
            api_url=os.environ.get("DRAWDORO_API_URL", defaults.api_url),
            api_key=os.environ.get("DRAWDORO_API_KEY", defaults.api_key),
            agent_name=os.environ.get("DRAWDORO_AGENT_NAME", defaults.agent_name),
            transport=Transport(os.environ.get("DRAWDORO_MCP_TRANSPORT", defaults.transport)),
            host=os.environ.get("DRAWDORO_MCP_HOST", defaults.host),
            port=int(os.environ.get("DRAWDORO_MCP_PORT", defaults.port)),
            allowed_hosts=_split(os.environ.get("DRAWDORO_MCP_ALLOWED_HOSTS", "")),
        )


def _split(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
