import uuid
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.domain.entities.models.documentation_page import DocumentationPage
from app.domain.usecases.documentation.get_documentation_page import GetDocumentationPage
from app.main.main import app
from app.presentation.factories.documentation_factories import get_documentation_page_factory


def test_should_get_documentation_page_when_found() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    diagram_id = uuid.uuid4()
    page = DocumentationPage(diagram_id=diagram_id, content="Hello world")
    mock_uc = AsyncMock(spec=GetDocumentationPage)
    mock_uc.execute.return_value = page
    app.dependency_overrides[get_documentation_page_factory] = lambda: mock_uc
    try:
        response = client.get(f"/diagrams/{diagram_id}/documentation")
        assert response.status_code == 200
        assert response.json()["content"] == "Hello world"
    finally:
        app.dependency_overrides.clear()
