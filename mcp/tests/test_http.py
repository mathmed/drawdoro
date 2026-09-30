from collections.abc import Iterator

import httpx
import pytest
from server import create_api, create_server, create_transport_security
from settings import Settings
from starlette.applications import Starlette
from starlette.testclient import TestClient
from tools.render import BrowserRenderer

PUBLIC_HOST = "diagrams.example"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    },
}
MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


@pytest.fixture
def sut() -> Starlette:
    settings = Settings(
        app_name="Acme Draw", api_url="http://api.test", allowed_hosts=(PUBLIC_HOST,)
    )
    api = create_api(settings, transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    return create_server(settings, api, BrowserRenderer(settings.frontend_url)).streamable_http_app(
        stateless_http=True, transport_security=create_transport_security(settings)
    )


@pytest.fixture
def public_client(sut: Starlette) -> Iterator[TestClient]:
    with TestClient(sut, base_url=f"https://{PUBLIC_HOST}") as client:
        yield client


def test_should_answer_health_check(public_client: TestClient) -> None:
    response = public_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_should_accept_the_allowed_public_host(public_client: TestClient) -> None:
    headers = {**MCP_HEADERS, "Origin": f"https://{PUBLIC_HOST}"}
    response = public_client.post("/mcp", json=INITIALIZE, headers=headers)
    assert response.status_code == 200
    assert '"name":"acme-draw"' in response.text


@pytest.mark.parametrize("base_url", ["http://localhost:8001", "http://127.0.0.1:8001"])
def test_should_accept_localhost(sut: Starlette, base_url: str) -> None:
    with TestClient(sut, base_url=base_url) as client:
        response = client.post("/mcp", json=INITIALIZE, headers=MCP_HEADERS)
        assert response.status_code == 200


def test_should_reject_unknown_host(sut: Starlette) -> None:
    with TestClient(sut, base_url="https://evil.example") as client:
        response = client.post("/mcp", json=INITIALIZE, headers=MCP_HEADERS)
        assert response.status_code == 421


def test_should_reject_unknown_origin(public_client: TestClient) -> None:
    headers = {**MCP_HEADERS, "Origin": "https://evil.example"}
    response = public_client.post("/mcp", json=INITIALIZE, headers=headers)
    assert response.status_code == 403


LIST_WORKSPACES = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "list_workspaces", "arguments": {}},
}


@pytest.fixture
def backend_keys() -> list[str | None]:
    return []


@pytest.fixture
def keyed_client(backend_keys: list[str | None]) -> Iterator[TestClient]:
    def backend(request: httpx.Request) -> httpx.Response:
        backend_keys.append(request.headers.get("X-API-Key"))
        return httpx.Response(200, json=[])

    settings = Settings(api_url="http://api.test", api_key="svc-key")
    api = create_api(settings, transport=httpx.MockTransport(backend))
    app = create_server(settings, api, BrowserRenderer(settings.frontend_url)).streamable_http_app(
        stateless_http=True, transport_security=create_transport_security(settings)
    )
    with TestClient(app, base_url="http://localhost:8001") as client:
        client.post("/mcp", json=INITIALIZE, headers=MCP_HEADERS)
        yield client


@pytest.mark.parametrize(
    "headers",
    [{"X-API-Key": "mcpk_ana"}, {"Authorization": "Bearer mcpk_ana"}],
)
def test_should_act_with_the_callers_personal_key(
    keyed_client: TestClient, backend_keys: list[str | None], headers: dict[str, str]
) -> None:
    response = keyed_client.post("/mcp", json=LIST_WORKSPACES, headers={**MCP_HEADERS, **headers})
    assert response.status_code == 200
    assert backend_keys == ["mcpk_ana"]


def test_should_fall_back_to_the_servers_key(
    keyed_client: TestClient, backend_keys: list[str | None]
) -> None:
    response = keyed_client.post("/mcp", json=LIST_WORKSPACES, headers=MCP_HEADERS)
    assert response.status_code == 200
    assert backend_keys == ["svc-key"]
