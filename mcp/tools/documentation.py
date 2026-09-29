import uuid

from pydantic import BaseModel
from tools.api import DrawdoroApi, JsonObject


class DocumentationContent(BaseModel):
    content: str


class DocumentationTools:
    def __init__(self, api: DrawdoroApi) -> None:
        self._api = api

    def get_documentation(self, diagram_id: uuid.UUID) -> JsonObject:
        """Get the Markdown documentation page of a diagram.

        A diagram that has no documentation yet answers 404; update_documentation creates it.

        Args:
            diagram_id: Diagram the page belongs to.
        """
        return self._api.get_object(f"/diagrams/{diagram_id}/documentation")

    def update_documentation(self, diagram_id: uuid.UUID, content: str) -> JsonObject:
        """Replace the Markdown documentation page of a diagram, creating it if needed.

        Args:
            diagram_id: Diagram the page belongs to.
            content: Complete Markdown content; it replaces the current page.
        """
        body = DocumentationContent(content=content)
        return self._api.put(f"/diagrams/{diagram_id}/documentation", body.model_dump())
