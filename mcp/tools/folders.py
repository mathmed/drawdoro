import uuid

from pydantic import BaseModel
from tools.api import DrawdoroApi, JsonObject


class NewFolder(BaseModel):
    name: str
    parent_folder_id: uuid.UUID | None = None


class FolderTools:
    def __init__(self, api: DrawdoroApi) -> None:
        self._api = api

    def list_folders(self, project_id: uuid.UUID) -> list[JsonObject]:
        """List every folder of a project.

        Folders nest through parent_folder_id, which is null for top-level folders.

        Args:
            project_id: Project whose folders to list.
        """
        return self._api.get_list(f"/projects/{project_id}/folders")

    def create_folder(
        self, project_id: uuid.UUID, name: str, parent_folder_id: uuid.UUID | None = None
    ) -> JsonObject:
        """Create a folder in a project.

        Args:
            project_id: Project that will own the folder.
            name: Folder name.
            parent_folder_id: Folder to nest it under; omit for a top-level folder.
        """
        body = NewFolder(name=name, parent_folder_id=parent_folder_id)
        return self._api.post(f"/projects/{project_id}/folders", body.model_dump(mode="json"))
