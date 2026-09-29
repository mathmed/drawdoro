import base64
import uuid
from typing import Any

import httpx
import pytest
from mcp.server.mcpserver import MCPServer
from mcp_types import ImageContent
from server import create_api, create_server
from settings import Settings
from tools.render import RenderRequest

from mcp import Client

TOOL_NAMES = {
    "list_workspaces",
    "list_projects",
    "get_project",
    "create_project",
    "list_folders",
    "create_folder",
    "list_diagrams",
    "get_diagram",
    "get_diagram_outline",
    "open_link",
    "create_diagram",
    "update_diagram",
    "edit_shapes",
    "render_diagram",
    "get_documentation",
    "update_documentation",
    "list_comments",
}


PNG = b"\x89PNG\r\n\x1a\n"
DIAGRAM_ID = uuid.uuid4()
# The API sends timestamps without an offset.
DIAGRAM: dict[str, Any] = {
    "id": str(DIAGRAM_ID),
    "project_id": str(uuid.uuid4()),
    "folder_id": None,
    "name": "Checkout",
    "canvas_state": {"store": {}, "schema": {}},
    "updated_at": "2026-09-29T21:54:58.694341",
}


class FakeBackend:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path.endswith("/projects"):
            return httpx.Response(200, json=[{"id": "p1"}])
        if request.url.path.endswith("/diagrams"):
            return httpx.Response(200, json=[DIAGRAM])
        if request.url.path == f"/diagrams/{DIAGRAM_ID}":
            return httpx.Response(200, json=DIAGRAM)
        return httpx.Response(404, json={"detail": "Diagram not found"})


class FakeRenderer:
    def render(self, canvas_state: dict[str, Any], request: RenderRequest) -> bytes:
        return PNG


@pytest.fixture
def api() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def sut(api: FakeBackend) -> MCPServer:
    settings = Settings(api_url="http://api.test", api_key="svc-key")
    return create_server(
        settings, create_api(settings, transport=httpx.MockTransport(api)), FakeRenderer()
    )


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
async def test_should_tell_agents_how_to_open_links(sut: MCPServer) -> None:
    async with Client(sut) as client:
        instructions = client.instructions
    assert instructions is not None
    assert "open_link" in instructions
    assert "list_workspaces" in instructions


def test_should_name_the_server_after_the_app() -> None:
    settings = Settings(app_name="Acme Draw", api_url="http://api.test")
    sut = create_server(settings, create_api(settings), FakeRenderer())
    assert sut.name == "acme-draw"
    assert sut.instructions is not None
    assert sut.instructions.startswith("Acme Draw holds")
    assert "shares a Acme Draw link" in sut.instructions


@pytest.mark.anyio
async def test_should_call_api_with_service_key(sut: MCPServer, api: FakeBackend) -> None:
    workspace_id = uuid.uuid4()
    async with Client(sut) as client:
        result = await client.call_tool("list_projects", {"workspace_id": str(workspace_id)})
    assert not result.is_error
    assert api.requests[0].url.path == f"/workspaces/{workspace_id}/projects"
    assert api.requests[0].headers["X-API-Key"] == "svc-key"
    assert api.requests[0].headers["X-Agent-Name"] == "Claude"


@pytest.mark.anyio
async def test_should_show_api_errors_to_the_model(sut: MCPServer) -> None:
    async with Client(sut) as client:
        result = await client.call_tool("get_diagram", {"diagram_id": str(uuid.uuid4())})
    assert result.is_error
    text = " ".join(getattr(item, "text", "") for item in result.content)
    assert "404" in text
    assert "Diagram not found" in text


@pytest.mark.anyio
async def test_should_reject_ids_that_are_not_uuids(sut: MCPServer, api: FakeBackend) -> None:
    async with Client(sut) as client:
        result = await client.call_tool("get_diagram", {"diagram_id": "../../workspaces"})
    assert result.is_error
    assert api.requests == []


@pytest.mark.anyio
async def test_should_list_diagrams_whose_timestamps_have_no_offset(sut: MCPServer) -> None:
    async with Client(sut) as client:
        result = await client.call_tool("list_diagrams", {"project_id": str(uuid.uuid4())})
    assert not result.is_error
    assert result.structured_content is not None
    [diagram] = result.structured_content["result"]
    assert diagram["updated_at"] == "2026-09-29T21:54:58.694341Z"


@pytest.mark.anyio
async def test_should_return_the_render_as_an_image(sut: MCPServer) -> None:
    async with Client(sut) as client:
        result = await client.call_tool("render_diagram", {"diagram_id": str(DIAGRAM_ID)})
    assert not result.is_error
    [image] = result.content
    assert isinstance(image, ImageContent)
    assert image.mime_type == "image/png"
    assert base64.b64decode(image.data) == PNG


def test_should_not_announce_agent_when_name_is_empty() -> None:
    fake = FakeBackend()
    settings = Settings(api_url="http://api.test", agent_name="")
    api = create_api(settings, transport=httpx.MockTransport(fake))
    api.get_list("/workspaces/w1/projects")
    assert "X-Agent-Name" not in fake.requests[0].headers
