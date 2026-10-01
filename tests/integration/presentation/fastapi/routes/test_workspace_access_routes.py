import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.entities.models.comment import Comment
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.project import Project
from app.domain.entities.models.user import User
from app.domain.entities.models.workspace import Workspace
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.entities.models.workspace_member_details import WorkspaceMemberDetails
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.comment.create_comment import CreateComment
from app.domain.usecases.diagram.get_diagram import GetDiagram
from app.domain.usecases.project.list_projects import ListProjects
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces
from app.domain.usecases.workspace_member.add_workspace_member import AddWorkspaceMember
from app.domain.usecases.workspace_member.list_workspace_members import ListWorkspaceMembers
from app.domain.usecases.workspace_member.remove_workspace_member import RemoveWorkspaceMember
from app.domain.usecases.workspace_member.update_workspace_member_role import (
    UpdateWorkspaceMemberRole,
)
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.comment_factories import create_comment_factory
from app.presentation.factories.diagram_factories import get_diagram_factory
from app.presentation.factories.project_factories import list_projects_factory
from app.presentation.factories.workspace_factories import list_workspaces_factory
from app.presentation.factories.workspace_member_factories import (
    add_workspace_member_factory,
    list_workspace_members_factory,
    remove_workspace_member_factory,
    update_workspace_member_role_factory,
)

USER = User(email="ana@example.com", name="Ana Souza")
WORKSPACE_ID = uuid.uuid4()
AUTH = {"Authorization": "Bearer good"}


@pytest.fixture
def authorize() -> AsyncMock:
    mock = AsyncMock(spec=AuthorizeWorkspaceAccess)
    mock.execute.return_value = WorkspaceMember(
        workspace_id=WORKSPACE_ID, user_id=USER.id, role=WorkspaceRole.OWNER
    )
    return mock


@pytest.fixture
def client(authorize: AsyncMock) -> Iterator[TestClient]:
    authenticate = AsyncMock(spec=AuthenticateUser)
    authenticate.execute.return_value = USER
    projects = AsyncMock(spec=ListProjects)
    projects.execute.return_value = [Project(workspace_id=WORKSPACE_ID, name="P")]
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=True)
    app.dependency_overrides[authenticate_user_factory] = lambda: authenticate
    app.dependency_overrides[authorize_workspace_access_factory] = lambda: authorize
    app.dependency_overrides[list_projects_factory] = lambda: projects
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_should_allow_members(client: TestClient, authorize: AsyncMock) -> None:
    assert client.get(f"/workspaces/{WORKSPACE_ID}/projects", headers=AUTH).status_code == 200
    params = authorize.execute.await_args.args[0]
    assert (params.user_id, params.workspace_id, params.required_role) == (
        USER.id,
        WORKSPACE_ID,
        WorkspaceRole.VIEWER,
    )


def test_should_require_editor_for_writes(client: TestClient, authorize: AsyncMock) -> None:
    client.post(f"/workspaces/{WORKSPACE_ID}/projects", headers=AUTH, json={"name": "New"})
    assert authorize.execute.await_args.args[0].required_role == WorkspaceRole.EDITOR


def test_should_hide_workspaces_from_non_members(client: TestClient, authorize: AsyncMock) -> None:
    authorize.execute.side_effect = NotFoundError("Workspace not found")
    assert client.get(f"/workspaces/{WORKSPACE_ID}/projects", headers=AUTH).status_code == 404


def test_should_forbid_insufficient_roles(client: TestClient, authorize: AsyncMock) -> None:
    authorize.execute.side_effect = ForbiddenError("This action requires the owner role")
    assert client.delete(f"/workspaces/{WORKSPACE_ID}", headers=AUTH).status_code == 403


def test_should_list_only_the_users_workspaces(client: TestClient) -> None:
    workspaces = AsyncMock(spec=ListWorkspaces)
    workspaces.execute.return_value = [Workspace(name="Mine", slug="mine")]
    app.dependency_overrides[list_workspaces_factory] = lambda: workspaces
    assert client.get("/workspaces", headers=AUTH).status_code == 200
    assert workspaces.execute.await_args.args[0].user_id == USER.id


def test_should_manage_members(client: TestClient) -> None:
    details = WorkspaceMemberDetails(
        user_id=USER.id, name=USER.name, email=USER.email, role=WorkspaceRole.OWNER
    )
    listing = AsyncMock(spec=ListWorkspaceMembers)
    listing.execute.return_value = [details]
    adding = AsyncMock(spec=AddWorkspaceMember)
    adding.execute.return_value = details
    updating = AsyncMock(spec=UpdateWorkspaceMemberRole)
    removing = AsyncMock(spec=RemoveWorkspaceMember)
    app.dependency_overrides[list_workspace_members_factory] = lambda: listing
    app.dependency_overrides[add_workspace_member_factory] = lambda: adding
    app.dependency_overrides[update_workspace_member_role_factory] = lambda: updating
    app.dependency_overrides[remove_workspace_member_factory] = lambda: removing
    base = f"/workspaces/{WORKSPACE_ID}/members"

    assert client.get(base, headers=AUTH).json()[0]["email"] == USER.email
    assert (
        client.post(base, headers=AUTH, json={"email": USER.email, "role": "viewer"}).status_code
        == 201
    )
    assert client.put(f"{base}/{USER.id}", headers=AUTH, json={"role": "editor"}).status_code == 204
    assert client.delete(f"{base}/{USER.id}", headers=AUTH).status_code == 204
    assert removing.execute.await_args.args[0].acting_user_id == USER.id


def test_should_record_signed_in_user_as_comment_author(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    creating = AsyncMock(spec=CreateComment)
    creating.execute.return_value = Comment(
        diagram_id=diagram_id, element_id="el", content="Hi", author_id=USER.id
    )
    app.dependency_overrides[create_comment_factory] = lambda: creating
    body = {"element_id": "el", "content": "Hi", "author_id": str(uuid.uuid4())}
    assert (
        client.post(f"/diagrams/{diagram_id}/comments", headers=AUTH, json=body).status_code == 201
    )
    assert creating.execute.await_args.args[0].actor.user_id == USER.id


def test_should_authorize_diagram_links_through_the_diagram(
    client: TestClient, authorize: AsyncMock
) -> None:
    diagram = Diagram(project_id=uuid.uuid4(), name="Linked")
    getting = AsyncMock(spec=GetDiagram)
    getting.execute.return_value = diagram
    app.dependency_overrides[get_diagram_factory] = lambda: getting
    assert client.get(f"/diagrams/{diagram.id}", headers=AUTH).status_code == 200
    params = authorize.execute.await_args.args[0]
    assert (params.diagram_id, params.project_id, params.required_role) == (
        diagram.id,
        None,
        WorkspaceRole.VIEWER,
    )
    authorize.execute.side_effect = NotFoundError("Diagram not found")
    assert client.get(f"/diagrams/{diagram.id}", headers=AUTH).status_code == 404
