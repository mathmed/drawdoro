import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project import Project
from app.domain.entities.models.workspace import Workspace
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.usecases.diagram.create_diagram import CreateDiagram
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.update_diagram import UpdateDiagram
from app.domain.usecases.folder.create_folder import CreateFolder
from app.domain.usecases.folder.update_folder import UpdateFolder
from app.domain.usecases.project.create_project import CreateProject
from app.domain.usecases.workspace.create_workspace import CreateWorkspace
from app.domain.usecases.workspace.update_workspace import UpdateWorkspace
from app.domain.usecases.workspace_member.add_workspace_member import AddWorkspaceMember
from app.main.main import app
from app.presentation.factories.diagram_factories import (
    create_diagram_factory,
    get_diagram_by_share_token_factory,
    update_diagram_factory,
)
from app.presentation.factories.folder_factories import create_folder_factory, update_folder_factory
from app.presentation.factories.project_factories import create_project_factory
from app.presentation.factories.workspace_factories import (
    create_workspace_factory,
    update_workspace_factory,
)
from app.presentation.factories.workspace_member_factories import add_workspace_member_factory

ID = uuid.uuid4()


# A request whose text carries NUL characters, which Postgres can't store, and the text the use
# case must receive instead.
@dataclass(frozen=True)
class TextCase:
    method: str
    path: str
    factory: Callable[..., object]
    use_case: type[object]
    result: object
    body: dict[str, object] | None
    expected: dict[str, str]


CASES = {
    "create-workspace": TextCase(
        "POST",
        "/workspaces",
        create_workspace_factory,
        CreateWorkspace,
        Workspace(name="Acme", slug="acme"),
        {"name": "Ac\x00me", "slug": "ac\x00me"},
        {"name": "Acme", "slug": "acme"},
    ),
    "update-workspace": TextCase(
        "PUT",
        f"/workspaces/{ID}",
        update_workspace_factory,
        UpdateWorkspace,
        Workspace(name="Acme", slug="acme"),
        {"name": "Acme\x00", "slug": "\x00acme"},
        {"name": "Acme", "slug": "acme"},
    ),
    "create-project": TextCase(
        "POST",
        f"/workspaces/{ID}/projects",
        create_project_factory,
        CreateProject,
        Project(workspace_id=ID, name="Shop"),
        {"name": "Sh\x00op", "description": "Online\x00 shop"},
        {"name": "Shop", "description": "Online shop"},
    ),
    "create-folder": TextCase(
        "POST",
        f"/projects/{ID}/folders",
        create_folder_factory,
        CreateFolder,
        Folder(project_id=ID, name="Docs"),
        {"name": "Do\x00cs"},
        {"name": "Docs"},
    ),
    "update-folder": TextCase(
        "PUT",
        f"/projects/{ID}/folders/{uuid.uuid4()}",
        update_folder_factory,
        UpdateFolder,
        Folder(project_id=ID, name="Docs"),
        {"name": "\x00Docs"},
        {"name": "Docs"},
    ),
    "create-diagram": TextCase(
        "POST",
        f"/projects/{ID}/diagrams",
        create_diagram_factory,
        CreateDiagram,
        Diagram(project_id=ID, name="Flow"),
        {"name": "Fl\x00ow"},
        {"name": "Flow"},
    ),
    "update-diagram": TextCase(
        "PUT",
        f"/projects/{ID}/diagrams/{uuid.uuid4()}",
        update_diagram_factory,
        UpdateDiagram,
        Diagram(project_id=ID, name="Flow"),
        {"name": "Flow\x00", "revision_summary": "Re\x00named"},
        {"name": "Flow", "revision_summary": "Renamed"},
    ),
    "add-member": TextCase(
        "POST",
        f"/workspaces/{ID}/members",
        add_workspace_member_factory,
        AddWorkspaceMember,
        WorkspaceMemberDetails(
            user_id=ID, name="Ada", email="ada@example.com", role=WorkspaceRole.EDITOR
        ),
        {"email": "ada@example.com\x00"},
        {"email": "ada@example.com"},
    ),
    "open-share-link": TextCase(
        "GET",
        "/share/tok%00en",
        get_diagram_by_share_token_factory,
        GetDiagramByShareToken,
        Diagram(project_id=ID, name="Flow"),
        None,
        {"share_token": "token"},
    ),
}


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


@pytest.mark.parametrize("case", CASES.values(), ids=CASES.keys())
def test_should_pass_text_without_nul_characters_to_the_use_case(
    client: TestClient, case: TextCase
) -> None:
    use_case = AsyncMock(spec=case.use_case)
    use_case.execute.return_value = case.result
    app.dependency_overrides[case.factory] = lambda: use_case
    response = client.request(case.method, case.path, json=case.body)
    assert response.is_success
    params = use_case.execute.await_args.args[0]
    assert {field: getattr(params, field) for field in case.expected} == case.expected
