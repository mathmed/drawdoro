import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from settings import Settings, Transport
from tools.api import DrawdoroApi
from tools.diagrams import DiagramTools
from tools.projects import ProjectTools

API_TIMEOUT_SECONDS = 30
# The server holds the service API key, so only local clients may reach it over HTTP.
LOCAL_ONLY = TransportSecuritySettings(
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"],
)


def create_api(settings: Settings, transport: httpx.BaseTransport | None = None) -> DrawdoroApi:
    headers = {"X-API-Key": settings.api_key} if settings.api_key else {}
    if settings.agent_name:
        headers["X-Agent-Name"] = settings.agent_name
    client = httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=API_TIMEOUT_SECONDS,
        transport=transport,
    )
    return DrawdoroApi(client)


def create_server(api: DrawdoroApi) -> MCPServer:
    server = MCPServer("drawdoro", description="MCP server for the Drawdoro diagramming tool")
    projects = ProjectTools(api)
    diagrams = DiagramTools(api)
    server.tool()(projects.list_projects)
    server.tool()(projects.get_project)
    server.tool()(diagrams.list_diagrams)
    server.tool()(diagrams.get_diagram)
    server.tool()(diagrams.update_diagram)
    return server


def main() -> None:
    settings = Settings.from_env()
    server = create_server(create_api(settings))
    if settings.transport == Transport.STDIO:
        server.run(transport="stdio")
        return
    server.run(
        transport="streamable-http",
        host=settings.host,
        port=settings.port,
        transport_security=LOCAL_ONLY,
    )


if __name__ == "__main__":
    main()
