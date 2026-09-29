import os

import pytest
from settings import LEGACY_PREFIX, Settings, Transport, slugify


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name == "APP_NAME" or name.startswith(("MCP_", LEGACY_PREFIX)):
            monkeypatch.delenv(name)


def test_should_use_defaults_when_env_is_empty() -> None:
    assert Settings.from_env() == Settings(
        app_name="Drawdoro",
        api_url="http://localhost:8000",
        api_key="",
        frontend_url="http://localhost:3000",
        agent_name="Claude",
        transport=Transport.STDIO,
        host="127.0.0.1",
        port=8001,
        allowed_hosts=(),
    )


def test_should_read_values_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "Acme Draw")
    monkeypatch.setenv("MCP_API_URL", "http://api:8000")
    monkeypatch.setenv("MCP_API_KEY", "svc-key")
    monkeypatch.setenv("MCP_FRONTEND_URL", "http://frontend:3000")
    monkeypatch.setenv("MCP_AGENT_NAME", "Cursor")
    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "diagrams.example, mcp.example ,")
    assert Settings.from_env() == Settings(
        app_name="Acme Draw",
        api_url="http://api:8000",
        api_key="svc-key",
        frontend_url="http://frontend:3000",
        agent_name="Cursor",
        transport=Transport.STREAMABLE_HTTP,
        host="0.0.0.0",
        port=9000,
        allowed_hosts=("diagrams.example", "mcp.example"),
    )


def test_should_fall_back_to_legacy_env_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRAWDORO_API_URL", "http://api:8000")
    monkeypatch.setenv("DRAWDORO_API_KEY", "svc-key")
    monkeypatch.setenv("DRAWDORO_FRONTEND_URL", "http://frontend:3000")
    monkeypatch.setenv("DRAWDORO_AGENT_NAME", "Cursor")
    monkeypatch.setenv("DRAWDORO_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("DRAWDORO_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("DRAWDORO_MCP_PORT", "9000")
    monkeypatch.setenv("DRAWDORO_MCP_ALLOWED_HOSTS", "diagrams.example")
    assert Settings.from_env() == Settings(
        api_url="http://api:8000",
        api_key="svc-key",
        frontend_url="http://frontend:3000",
        agent_name="Cursor",
        transport=Transport.STREAMABLE_HTTP,
        host="0.0.0.0",
        port=9000,
        allowed_hosts=("diagrams.example",),
    )


def test_should_prefer_neutral_env_names_over_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRAWDORO_API_URL", "http://legacy:8000")
    monkeypatch.setenv("MCP_API_URL", "http://api:8000")
    assert Settings.from_env().api_url == "http://api:8000"


def test_should_keep_empty_neutral_value_over_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRAWDORO_AGENT_NAME", "Cursor")
    monkeypatch.setenv("MCP_AGENT_NAME", "")
    assert Settings.from_env().agent_name == ""


def test_should_reject_unknown_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(ValueError, match="carrier-pigeon"):
        Settings.from_env()


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("Drawdoro", "drawdoro"),
        ("CondoDraw", "condodraw"),
        (" Acme  Draw! ", "acme-draw"),
        ("", "app"),
    ],
)
def test_should_derive_slug_from_app_name(name: str, slug: str) -> None:
    assert slugify(name) == slug
    assert Settings(app_name=name).app_slug == slug
