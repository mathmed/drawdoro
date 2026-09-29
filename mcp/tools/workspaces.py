from tools.api import DrawdoroApi, JsonObject


class WorkspaceTools:
    def __init__(self, api: DrawdoroApi) -> None:
        self._api = api

    def list_workspaces(self) -> list[JsonObject]:
        """List every Drawdoro workspace, the top level that groups projects.

        Start here when you know a project or diagram only by name.
        """
        return self._api.get_list("/workspaces")
