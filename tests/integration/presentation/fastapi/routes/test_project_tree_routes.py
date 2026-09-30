import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.diagram_summary import DiagramSummary
from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project_tree import ProjectTree
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.diagram.list_diagrams import ListDiagrams
from app.domain.usecases.project.get_project_tree import GetProjectTree, GetProjectTreeParams
from app.main.main import app
from app.presentation.factories.diagram_factories import list_diagrams_factory
from app.presentation.factories.project_factories import get_project_tree_factory

PROJECT_ID = uuid.uuid4()
NOW = datetime.now(UTC)
FOLDER = Folder(project_id=PROJECT_ID, name="Services")
SUMMARY = DiagramSummary(
    id=uuid.uuid4(),
    project_id=PROJECT_ID,
    folder_id=FOLDER.id,
    name="Payments",
    created_at=NOW,
    updated_at=NOW,
)


@pytest.fixture
def use_case() -> AsyncMock:
    return AsyncMock(spec=GetProjectTree)


@pytest.fixture
def client(use_case: AsyncMock) -> Iterator[TestClient]:
    app.dependency_overrides[get_project_tree_factory] = lambda: use_case
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_should_return_the_project_tree_in_one_response(
    client: TestClient, use_case: AsyncMock
) -> None:
    use_case.execute.return_value = ProjectTree(folders=[FOLDER], diagrams=[SUMMARY])

    response = client.get(f"/projects/{PROJECT_ID}/tree")

    assert response.status_code == 200
    body = response.json()
    assert [folder["name"] for folder in body["folders"]] == ["Services"]
    assert body["diagrams"] == [
        {
            "id": str(SUMMARY.id),
            "project_id": str(PROJECT_ID),
            "folder_id": str(FOLDER.id),
            "name": "Payments",
            "created_at": NOW.isoformat().replace("+00:00", "Z"),
            "updated_at": NOW.isoformat().replace("+00:00", "Z"),
        }
    ]
    use_case.execute.assert_awaited_once_with(GetProjectTreeParams(project_id=PROJECT_ID))


def test_should_return_404_when_project_tree_is_missing(
    client: TestClient, use_case: AsyncMock
) -> None:
    use_case.execute.side_effect = NotFoundError("Project not found")

    assert client.get(f"/projects/{PROJECT_ID}/tree").status_code == 404


def test_should_list_diagrams_without_their_content(client: TestClient) -> None:
    list_diagrams = AsyncMock(spec=ListDiagrams)
    list_diagrams.execute.return_value = [SUMMARY]
    app.dependency_overrides[list_diagrams_factory] = lambda: list_diagrams

    body = client.get(f"/projects/{PROJECT_ID}/diagrams").json()

    assert [diagram["name"] for diagram in body] == ["Payments"]
    assert "canvas_state" not in body[0]
    assert "semantic_metadata" not in body[0]
