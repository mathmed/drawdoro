from collections.abc import Callable

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from settings import Settings, Transport
from starlette.requests import Request
from starlette.responses import JSONResponse
from tools.api import BackendApi
from tools.comments import CommentTools
from tools.diagrams import DiagramTools
from tools.documentation import DocumentationTools
from tools.folders import FolderTools
from tools.projects import ProjectTools
from tools.render import BrowserRenderer, Renderer, RenderTools
from tools.workspaces import WorkspaceTools

API_TIMEOUT_SECONDS = 30
LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")
# Sent to the client on connect; agents read it to know when and how to use the tools.
INSTRUCTIONS = """{app_name} holds software architecture diagrams, organised as
workspace -> project -> folders (optional, nestable) -> diagram. Each diagram is a tldraw canvas
with an optional Markdown documentation page and comments anchored to its shapes.

When the user shares a {app_name} link, call open_link with it: /diagrams/<id> links open the
editable diagram, /share/<token> links a read-only copy. Given only names, find ids with
list_workspaces, list_projects, list_folders and list_diagrams.

Canvases are large, so prefer the compact tools: get_diagram_outline to read shapes and their text,
edit_shapes to create, change or delete only the records that change, and render_diagram to look
at the result as an image (check it after every edit). Use get_diagram and update_diagram, which
carry the complete canvas_state, only to rebuild a diagram wholesale."""


def create_api(settings: Settings, transport: httpx.BaseTransport | None = None) -> BackendApi:
    headers = {"X-API-Key": settings.api_key} if settings.api_key else {}
    if settings.agent_name:
        headers["X-Agent-Name"] = settings.agent_name
    client = httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=API_TIMEOUT_SECONDS,
        transport=transport,
    )
    return BackendApi(client, settings.app_name)


def create_transport_security(settings: Settings) -> TransportSecuritySettings:
    # The server holds the service API key: only localhost and the hosts explicitly routed to it
    # may reach it, which also blocks DNS rebinding from browsers.
    local_hosts = [f"{host}:*" for host in LOCAL_HOSTS]
    public_hosts = [pattern for host in settings.allowed_hosts for pattern in (host, f"{host}:*")]
    return TransportSecuritySettings(
        allowed_hosts=local_hosts + public_hosts,
        allowed_origins=[f"http://{host}" for host in local_hosts]
        + [f"https://{host}" for host in public_hosts],
    )


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def create_server(settings: Settings, api: BackendApi, renderer: Renderer) -> MCPServer:
    server = MCPServer(
        settings.app_slug,
        description=f"MCP server for the {settings.app_name} diagramming tool",
        instructions=INSTRUCTIONS.format(app_name=settings.app_name),
    )
    workspaces = WorkspaceTools(api)
    projects = ProjectTools(api)
    folders = FolderTools(api)
    diagrams = DiagramTools(api)
    render = RenderTools(api, renderer)
    documentation = DocumentationTools(api)
    comments = CommentTools(api)
    tools: list[Callable[..., object]] = [
        workspaces.list_workspaces,
        projects.list_projects,
        projects.get_project,
        projects.create_project,
        folders.list_folders,
        folders.create_folder,
        diagrams.list_diagrams,
        diagrams.get_diagram,
        diagrams.get_diagram_outline,
        diagrams.open_link,
        diagrams.create_diagram,
        diagrams.update_diagram,
        diagrams.edit_shapes,
        render.render_diagram,
        documentation.get_documentation,
        documentation.update_documentation,
        comments.list_comments,
    ]
    for tool in tools:
        server.tool()(tool)
    server.custom_route("/health", methods=["GET"])(health)
    return server


def main() -> None:
    settings = Settings.from_env()
    server = create_server(settings, create_api(settings), BrowserRenderer(settings.frontend_url))
    if settings.transport == Transport.STDIO:
        server.run(transport="stdio")
        return
    # Stateless: the tools are plain request/response, so restarts and extra replicas lose nothing.
    server.run(
        transport="streamable-http",
        host=settings.host,
        port=settings.port,
        stateless_http=True,
        transport_security=create_transport_security(settings),
    )


if __name__ == "__main__":
    main()
