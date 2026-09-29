import uuid

import httpx
import pytest
from mcp.server.mcpserver import MCPServer
from server import create_api, create_server
from settings import Settings

from mcp import Client

TOOL_NAMES = {"list_projects", "get_project", "list_diagrams", "get_diagram", "update_diagram"}


class FakeDrawdoro:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path.endswith("/projects"):
            return httpx.Response(200, json=[{"id": "p1"}])
        return httpx.Response(404, json={"detail": "Diagram not found"})


@pytest.fixture
def api() -> FakeDrawdoro:
    return FakeDrawdoro()


@pytest.fixture
def sut(api: FakeDrawdoro) -> MCPServer:
    settings = Settings(api_url="http://drawdoro.test", api_key="svc-key")
    return create_server(create_api(settings, transport=httpx.MockTransport(api)))


@pytest.mark.anyio
async def test_should_register_every_tool_with_a_description(sut: MCPServer) -> None:
    async with Client(sut) as client:
        tools = (await client.list_tools()).tools
    assert {tool.name for tool in tools} == TOOL_NAMES
    assert all(tool.description for tool in tools)
    update = next(tool for tool in tools if tool.name == "update_diagram")
    assert update.description is not None
    assert "omitted ones keep their current values" in update.description
    assert "canvas_state: Complete tldraw store snapshot" in update.description
    assert all("self" not in tool.input_schema["properties"] for tool in tools)


@pytest.mark.anyio
async def test_should_call_api_with_service_key(sut: MCPServer, api: FakeDrawdoro) -> None:
    workspace_id = uuid.uuid4()
    async with Client(sut) as client:
        result = await client.call_tool("list_projects", {"workspace_id": str(workspace_id)})
    assert not result.is_error
    assert api.requests[0].url.path == f"/workspaces/{workspace_id}/projects"
    assert api.requests[0].headers["X-API-Key"] == "svc-key"
    assert api.requests[0].headers["X-Agent-Name"] == "Claude"


@pytest.mark.anyio
async def test_should_show_api_errors_to_the_model(sut: MCPServer) -> None:
    arguments = {"project_id": str(uuid.uuid4()), "diagram_id": str(uuid.uuid4())}
    async with Client(sut) as client:
        result = await client.call_tool("get_diagram", arguments)
    assert result.is_error
    text = " ".join(getattr(item, "text", "") for item in result.content)
    assert "404" in text
    assert "Diagram not found" in text


@pytest.mark.anyio
async def test_should_reject_ids_that_are_not_uuids(sut: MCPServer, api: FakeDrawdoro) -> None:
    arguments = {"project_id": str(uuid.uuid4()), "diagram_id": "../../workspaces"}
    async with Client(sut) as client:
        result = await client.call_tool("get_diagram", arguments)
    assert result.is_error
    assert api.requests == []


def test_should_not_announce_agent_when_name_is_empty() -> None:
    fake = FakeDrawdoro()
    settings = Settings(api_url="http://drawdoro.test", agent_name="")
    api = create_api(settings, transport=httpx.MockTransport(fake))
    api.get_list("/workspaces/w1/projects")
    assert "X-Agent-Name" not in fake.requests[0].headers
