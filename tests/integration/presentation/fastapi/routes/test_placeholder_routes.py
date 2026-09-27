import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project import Project
from app.domain.entities.models.template import Template
from app.domain.entities.models.workspace import Workspace
from app.domain.usecases.comment.list_comments import ListComments
from app.domain.usecases.diagram.list_diagrams import ListDiagrams
from app.domain.usecases.documentation.get_documentation_page import GetDocumentationPage
from app.domain.usecases.folder.list_folders import ListFolders
from app.domain.usecases.project.list_projects import ListProjects
from app.domain.usecases.template.list_templates import ListTemplates
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces
from app.main.main import app
from app.presentation.factories.comment_factories import list_comments_factory
from app.presentation.factories.diagram_factories import list_diagrams_factory
from app.presentation.factories.documentation_factories import get_documentation_page_factory
from app.presentation.factories.folder_factories import list_folders_factory
from app.presentation.factories.project_factories import list_projects_factory
from app.presentation.factories.template_factories import list_templates_factory
from app.presentation.factories.workspace_factories import list_workspaces_factory


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_should_return_200_for_list_workspaces(client: TestClient) -> None:
    mock_uc = AsyncMock(spec=ListWorkspaces)
    mock_uc.execute.return_value = [Workspace(name="W", slug="w")]
    app.dependency_overrides[list_workspaces_factory] = lambda: mock_uc
    try:
        response = client.get("/workspaces")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_200_for_list_projects(client: TestClient) -> None:
    workspace_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=ListProjects)
    mock_uc.execute.return_value = [Project(workspace_id=workspace_id, name="P")]
    app.dependency_overrides[list_projects_factory] = lambda: mock_uc
    try:
        response = client.get(f"/workspaces/{workspace_id}/projects")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_200_for_list_folders(client: TestClient) -> None:
    project_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=ListFolders)
    mock_uc.execute.return_value = [Folder(project_id=project_id, name="F")]
    app.dependency_overrides[list_folders_factory] = lambda: mock_uc
    try:
        response = client.get(f"/projects/{project_id}/folders")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_200_for_list_diagrams(client: TestClient) -> None:
    project_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=ListDiagrams)
    mock_uc.execute.return_value = [Diagram(project_id=project_id, name="D")]
    app.dependency_overrides[list_diagrams_factory] = lambda: mock_uc
    try:
        response = client.get(f"/projects/{project_id}/diagrams")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_404_for_get_documentation_when_not_found(client: TestClient) -> None:
    from app.domain.errors.domain_errors import NotFoundError

    diagram_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=GetDocumentationPage)
    mock_uc.execute.side_effect = NotFoundError("not found")
    app.dependency_overrides[get_documentation_page_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram_id}/documentation")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_should_return_200_for_list_comments(client: TestClient) -> None:
    diagram_id = uuid.uuid4()
    mock_uc = AsyncMock(spec=ListComments)
    mock_uc.execute.return_value = []
    app.dependency_overrides[list_comments_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram_id}/comments")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_should_return_200_for_list_templates(client: TestClient) -> None:
    mock_uc = AsyncMock(spec=ListTemplates)
    mock_uc.execute.return_value = [Template(name="T")]
    app.dependency_overrides[list_templates_factory] = lambda: mock_uc
    try:
        response = client.get("/templates")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
