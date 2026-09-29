import uuid

from pydantic import BaseModel
from tools.api import DrawdoroApi, JsonObject


class NewProject(BaseModel):
    name: str
    description: str = ""


class ProjectTools:
    def __init__(self, api: DrawdoroApi) -> None:
        self._api = api

    def list_projects(self, workspace_id: uuid.UUID) -> list[JsonObject]:
        """List the projects of a workspace.

        Args:
            workspace_id: Workspace that owns the projects.
        """
        return self._api.get_list(f"/workspaces/{workspace_id}/projects")

    def get_project(self, workspace_id: uuid.UUID, project_id: uuid.UUID) -> JsonObject:
        """Get one project of a workspace.

        Args:
            workspace_id: Workspace that owns the project.
            project_id: Project to fetch.
        """
        return self._api.get_object(f"/workspaces/{workspace_id}/projects/{project_id}")

    def create_project(
        self, workspace_id: uuid.UUID, name: str, description: str = ""
    ) -> JsonObject:
        """Create a project in a workspace.

        Args:
            workspace_id: Workspace that will own the project.
            name: Project name.
            description: Short description shown in the project overview.
        """
        body = NewProject(name=name, description=description)
        return self._api.post(f"/workspaces/{workspace_id}/projects", body.model_dump(mode="json"))
