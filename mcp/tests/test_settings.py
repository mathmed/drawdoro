import pytest
from settings import Settings, Transport

ENV_VARS = (
    "DRAWDORO_API_URL",
    "DRAWDORO_API_KEY",
    "DRAWDORO_FRONTEND_URL",
    "DRAWDORO_AGENT_NAME",
    "DRAWDORO_MCP_TRANSPORT",
    "DRAWDORO_MCP_HOST",
    "DRAWDORO_MCP_PORT",
    "DRAWDORO_MCP_ALLOWED_HOSTS",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_should_use_defaults_when_env_is_empty() -> None:
    assert Settings.from_env() == Settings(
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
    monkeypatch.setenv("DRAWDORO_API_URL", "http://api:8000")
    monkeypatch.setenv("DRAWDORO_API_KEY", "svc-key")
    monkeypatch.setenv("DRAWDORO_FRONTEND_URL", "http://frontend:3000")
    monkeypatch.setenv("DRAWDORO_AGENT_NAME", "Cursor")
    monkeypatch.setenv("DRAWDORO_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("DRAWDORO_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("DRAWDORO_MCP_PORT", "9000")
    monkeypatch.setenv("DRAWDORO_MCP_ALLOWED_HOSTS", "drawdoro.example, mcp.example ,")
    assert Settings.from_env() == Settings(
        api_url="http://api:8000",
        api_key="svc-key",
        frontend_url="http://frontend:3000",
        agent_name="Cursor",
        transport=Transport.STREAMABLE_HTTP,
        host="0.0.0.0",
        port=9000,
        allowed_hosts=("drawdoro.example", "mcp.example"),
    )


def test_should_reject_unknown_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRAWDORO_MCP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(ValueError, match="carrier-pigeon"):
        Settings.from_env()
