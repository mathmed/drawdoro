import uuid

from tools.api import BackendApi, JsonObject


class CommentTools:
    def __init__(self, api: BackendApi) -> None:
        self._api = api

    def list_comments(self, diagram_id: uuid.UUID) -> list[JsonObject]:
        """List the comments of a diagram.

        Each comment is anchored to a shape through element_id, the shape's record id in the
        diagram's canvas_state.

        Args:
            diagram_id: Diagram whose comments to list.
        """
        return self._api.get_list(f"/diagrams/{diagram_id}/comments")
