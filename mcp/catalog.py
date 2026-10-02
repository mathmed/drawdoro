from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations


class ToolArea(StrEnum):
    STRUCTURE = "structure"
    DIAGRAMS = "diagrams"
    CANVAS = "canvas"
    RENDER = "render"
    HISTORY = "history"
    DOCUMENTATION = "documentation"
    COMMENTS = "comments"
    GALLERY = "gallery"


class Requirement(StrEnum):
    # Only works with the person's own key: the shared service key has no owner.
    PERSONAL_KEY = "personal_key"
    # Needs the editor (or owner) role in the workspace it writes to.
    EDITOR_ROLE = "editor_role"


# Shown to people in the order listed, e.g. in the frontend's list of available tools.
AREA_TITLES: dict[ToolArea, str] = {
    ToolArea.STRUCTURE: "Workspaces, projects and folders",
    ToolArea.DIAGRAMS: "Diagrams",
    ToolArea.CANVAS: "Canvas and shapes",
    ToolArea.RENDER: "Rendering and links",
    ToolArea.HISTORY: "History",
    ToolArea.DOCUMENTATION: "Documentation",
    ToolArea.COMMENTS: "Comments",
    ToolArea.GALLERY: "Personal gallery",
}


# One tool of the server and what people need to know about it besides its docstring. The
# docstring stays the description the model reads; this is the metadata around it.
@dataclass(frozen=True)
class ToolEntry:
    function: Callable[..., object]
    area: ToolArea
    requires: tuple[Requirement, ...] = ()
    read_only: bool = True
    destructive: bool = False

    @property
    def name(self) -> str:
        return self.function.__name__

    def annotations(self) -> ToolAnnotations:
        return ToolAnnotations(read_only_hint=self.read_only, destructive_hint=self.destructive)

    def meta(self) -> dict[str, object]:
        return {"area": str(self.area), "requires": [str(r) for r in self.requires]}


def register(server: MCPServer, entries: list[ToolEntry]) -> None:
    for entry in entries:
        server.tool(annotations=entry.annotations(), meta=entry.meta())(entry.function)
