import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock, NonCallableMagicMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.documentation_page_repository import DocumentationPageRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.user_repository import UserRepository
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.contracts.workspace_repository import WorkspaceRepository
from app.domain.entities.models.user import User
from app.domain.usecases.auth.authenticate_api_key import AuthenticateApiKey
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.documentation.upsert_documentation_page import UpsertDocumentationPage
from app.domain.usecases.project.create_project import CreateProject
from app.domain.usecases.workspace_member.add_workspace_member import AddWorkspaceMember
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_api_key_factory,
    authenticate_user_factory,
)
from app.presentation.factories.documentation_factories import upsert_documentation_page_factory
from app.presentation.factories.project_factories import create_project_factory
from app.presentation.factories.workspace_member_factories import add_workspace_member_factory
from tests.doubles import double

SERVICE_KEY = "service-secret"
MISSING = uuid.uuid4()

# The callers workspace access lets through without checking the path's workspace or diagram: the
# trusted service key (the MCP server) and anyone while authentication is off.
CALLERS = {
    "service-key": (
        Settings(auth_enabled=True, service_api_key=SERVICE_KEY),
        {"X-API-Key": SERVICE_KEY},
    ),
    "auth-off": (Settings(auth_enabled=False), {}),
}


@pytest.fixture(params=CALLERS.keys())
def headers(request: pytest.FixtureRequest) -> Iterator[dict[str, str]]:
    settings, headers = CALLERS[request.param]
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[authenticate_user_factory] = lambda: AsyncMock(spec=AuthenticateUser)
    app.dependency_overrides[authenticate_api_key_factory] = lambda: AsyncMock(
        spec=AuthenticateApiKey
    )
    yield headers
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def workspaces() -> NonCallableMagicMock:
    repo = double(WorkspaceRepository)
    repo.exists_including_deleted.return_value = False
    return repo


def test_should_return_404_when_creating_a_project_in_a_missing_workspace(
    client: TestClient, headers: dict[str, str], workspaces: NonCallableMagicMock
) -> None:
    projects = double(ProjectRepository)
    app.dependency_overrides[create_project_factory] = lambda: CreateProject(projects, workspaces)
    response = client.post(f"/workspaces/{MISSING}/projects", headers=headers, json={"name": "S"})
    assert response.status_code == 404
    assert response.json() == {"detail": f"Workspace {MISSING} not found"}
    projects.create.assert_not_awaited()


def test_should_return_404_when_adding_a_member_to_a_missing_workspace(
    client: TestClient, headers: dict[str, str], workspaces: NonCallableMagicMock
) -> None:
    members = double(WorkspaceMemberRepository)
    users = double(UserRepository)
    users.get_by_email.return_value = User(email="ada@example.com", name="Ada")
    app.dependency_overrides[add_workspace_member_factory] = lambda: AddWorkspaceMember(
        members, users, workspaces, "Drawdoro"
    )
    response = client.post(
        f"/workspaces/{MISSING}/members", headers=headers, json={"email": "ada@example.com"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Workspace {MISSING} not found"}
    members.create.assert_not_awaited()


def test_should_return_404_when_writing_the_documentation_of_a_missing_diagram(
    client: TestClient, headers: dict[str, str]
) -> None:
    pages = double(DocumentationPageRepository)
    diagrams = double(DiagramRepository)
    diagrams.exists.return_value = False
    app.dependency_overrides[upsert_documentation_page_factory] = lambda: UpsertDocumentationPage(
        pages, diagrams
    )
    response = client.put(
        f"/diagrams/{MISSING}/documentation", headers=headers, json={"content": "# Flow"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Diagram {MISSING} not found"}
    pages.upsert.assert_not_awaited()


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/workspaces/{workspace_id}/projects", "post"),
        ("/workspaces/{workspace_id}/members", "post"),
        ("/diagrams/{diagram_id}/documentation", "put"),
    ],
)
def test_should_document_the_missing_workspace_or_diagram(path: str, method: str) -> None:
    not_found = app.openapi()["paths"][path][method]["responses"]["404"]
    assert not_found["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
