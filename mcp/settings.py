import os
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

# Env var prefix used before the settings became brand-neutral; still read so existing setups work.
LEGACY_PREFIX = "DRAWDORO_"
LEGACY_NAMES = {
    "MCP_API_URL": "API_URL",
    "MCP_API_KEY": "API_KEY",
    "MCP_FRONTEND_URL": "FRONTEND_URL",
    "MCP_AGENT_NAME": "AGENT_NAME",
}


class Transport(StrEnum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


@dataclass(frozen=True)
class Settings:
    # Product name shown to agents; the white-label point shared with the API and the frontend.
    app_name: str = "Drawdoro"
    api_url: str = "http://localhost:8000"
    api_key: str = ""
    # render_diagram opens this frontend's /render page in a headless browser.
    frontend_url: str = "http://localhost:3000"
    # Shown to people with the diagram open while the agent works on it; empty hides it.
    agent_name: str = "Claude"
    transport: Transport = Transport.STDIO
    host: str = "127.0.0.1"
    port: int = 8001
    # Public hostnames accepted over HTTP besides localhost, e.g. the one routed by the ingress.
    allowed_hosts: tuple[str, ...] = ()

    @property
    def app_slug(self) -> str:
        return slugify(self.app_name)

    @classmethod
    def from_env(cls) -> Self:
        defaults = cls()
        return cls(
            app_name=os.environ.get("APP_NAME", defaults.app_name),
            api_url=_env("MCP_API_URL", defaults.api_url),
            api_key=_env("MCP_API_KEY", defaults.api_key),
            frontend_url=_env("MCP_FRONTEND_URL", defaults.frontend_url),
            agent_name=_env("MCP_AGENT_NAME", defaults.agent_name),
            transport=Transport(_env("MCP_TRANSPORT", defaults.transport)),
            host=_env("MCP_HOST", defaults.host),
            port=int(_env("MCP_PORT", str(defaults.port))),
            allowed_hosts=_split(_env("MCP_ALLOWED_HOSTS", "")),
        )


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "app"


def _env(name: str, default: str) -> str:
    if name in os.environ:
        return os.environ[name]
    legacy = LEGACY_PREFIX + LEGACY_NAMES.get(name, name)
    return os.environ.get(legacy, default)


def _split(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())
