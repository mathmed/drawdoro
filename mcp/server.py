import os

from mcp.server.fastmcp import FastMCP
from tools.diagrams import get_diagram, list_diagrams, update_diagram
from tools.projects import get_project, list_projects

API_URL = os.environ.get("DRAWDORO_API_URL", "http://localhost:8000")

mcp = FastMCP("drawdoro", description="MCP server for the Drawdoro diagramming tool")

mcp.tool()(get_diagram)
mcp.tool()(list_diagrams)
mcp.tool()(update_diagram)
mcp.tool()(list_projects)
mcp.tool()(get_project)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
