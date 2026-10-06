import base64
import uuid
from collections.abc import Iterator
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.entities.models.user import User
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.thumbnail_theme import ThumbnailTheme
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import (
    ForbiddenError,
    InvalidInputError,
    NotFoundError,
    PayloadTooLargeError,
)
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.diagram.get_diagram import GetDiagram
from app.domain.usecases.diagram.list_diagram_thumbnails import ListDiagramThumbnails
from app.domain.usecases.diagram.save_diagram_thumbnail import SaveDiagramThumbnail
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.diagram_factories import (
    get_diagram_factory,
    list_diagram_thumbnails_factory,
    save_diagram_thumbnail_factory,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
PROJECT_ID = uuid.uuid4()
DIAGRAM_ID = uuid.uuid4()
VERSION = "2026-10-06T12:30:00.123456"
USER = User(email="ana@example.com", name="Ana Souza")
AUTH = {"Authorization": "Bearer good"}


@pytest.fixture
def listing() -> AsyncMock:
    mock = AsyncMock(spec=ListDiagramThumbnails)
    mock.execute.return_value = [
        DiagramThumbnail(
            diagram_id=DIAGRAM_ID,
            theme=ThumbnailTheme.DARK,
            version=datetime.fromisoformat(VERSION),
            image=PNG,
            mime_type=ImageMimeType.PNG,
        )
    ]
    return mock


@pytest.fixture
def saving() -> AsyncMock:
    return AsyncMock(spec=SaveDiagramThumbnail)


@pytest.fixture
def client(listing: AsyncMock, saving: AsyncMock) -> Iterator[TestClient]:
    app.dependency_overrides[list_diagram_thumbnails_factory] = lambda: listing
    app.dependency_overrides[save_diagram_thumbnail_factory] = lambda: saving
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_should_list_the_project_thumbnails_as_base64_in_the_requested_theme(
    client: TestClient, listing: AsyncMock
) -> None:
    get_diagram = AsyncMock(spec=GetDiagram)
    app.dependency_overrides[get_diagram_factory] = lambda: get_diagram

    response = client.get(f"/projects/{PROJECT_ID}/diagrams/thumbnails", params={"theme": "dark"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "diagram_id": str(DIAGRAM_ID),
            "version": VERSION,
            "mime_type": "image/png",
            "image_base64": base64.b64encode(PNG).decode(),
        }
    ]
    params = listing.execute.await_args.args[0]
    assert (params.project_id, params.theme) == (PROJECT_ID, ThumbnailTheme.DARK)
    # "thumbnails" never reaches the route of a single diagram.
    get_diagram.execute.assert_not_awaited()


def test_should_list_light_thumbnails_by_default(client: TestClient, listing: AsyncMock) -> None:
    assert client.get(f"/projects/{PROJECT_ID}/diagrams/thumbnails").status_code == 200
    assert listing.execute.await_args.args[0].theme == ThumbnailTheme.LIGHT


def test_should_reject_an_unknown_theme(client: TestClient, listing: AsyncMock) -> None:
    response = client.get(f"/projects/{PROJECT_ID}/diagrams/thumbnails", params={"theme": "sepia"})

    assert response.status_code == 422
    listing.execute.assert_not_awaited()


def test_should_save_both_themes_of_a_thumbnail(client: TestClient, saving: AsyncMock) -> None:
    encoded = base64.b64encode(PNG).decode()

    response = client.put(
        f"/diagrams/{DIAGRAM_ID}/thumbnail",
        json={"version": VERSION, "light_base64": encoded, "dark_base64": encoded},
    )

    assert response.status_code == 204
    assert response.content == b""
    params = saving.execute.await_args.args[0]
    assert params.diagram_id == DIAGRAM_ID
    assert params.version == datetime.fromisoformat(VERSION)
    assert (params.light, params.dark) == (PNG, PNG)


def test_should_save_an_empty_diagram_without_images(client: TestClient, saving: AsyncMock) -> None:
    response = client.put(f"/diagrams/{DIAGRAM_ID}/thumbnail", json={"version": VERSION})

    assert response.status_code == 204
    params = saving.execute.await_args.args[0]
    assert (params.light, params.dark) == (None, None)


@pytest.mark.parametrize(
    "body",
    [{}, {"version": "yesterday"}, {"version": VERSION, "light_base64": "not base64!"}],
)
def test_should_reject_malformed_thumbnail_uploads(
    client: TestClient, saving: AsyncMock, body: dict[str, str]
) -> None:
    assert client.put(f"/diagrams/{DIAGRAM_ID}/thumbnail", json=body).status_code == 422
    saving.execute.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (PayloadTooLargeError("The light thumbnail is too large (limit 65536 bytes)"), 413),
        (InvalidInputError("The light thumbnail must be a PNG or WebP image"), 422),
        (NotFoundError("Diagram not found"), 404),
    ],
)
def test_should_translate_thumbnail_errors(
    client: TestClient, saving: AsyncMock, error: Exception, status_code: int
) -> None:
    saving.execute.side_effect = error

    response = client.put(f"/diagrams/{DIAGRAM_ID}/thumbnail", json={"version": VERSION})

    assert response.status_code == status_code


@pytest.fixture
def authorize() -> AsyncMock:
    mock = AsyncMock(spec=AuthorizeWorkspaceAccess)
    mock.execute.return_value = WorkspaceMember(
        workspace_id=uuid.uuid4(), user_id=USER.id, role=WorkspaceRole.VIEWER
    )
    return mock


@pytest.fixture
def signed_in(client: TestClient, authorize: AsyncMock) -> TestClient:
    authenticate = AsyncMock(spec=AuthenticateUser)
    authenticate.execute.return_value = USER
    app.dependency_overrides[get_settings] = lambda: Settings(auth_enabled=True)
    app.dependency_overrides[authenticate_user_factory] = lambda: authenticate
    app.dependency_overrides[authorize_workspace_access_factory] = lambda: authorize
    return client


def test_should_let_any_member_read_the_thumbnails(
    signed_in: TestClient, authorize: AsyncMock
) -> None:
    response = signed_in.get(f"/projects/{PROJECT_ID}/diagrams/thumbnails", headers=AUTH)

    assert response.status_code == 200
    params = authorize.execute.await_args.args[0]
    assert (params.project_id, params.required_role) == (PROJECT_ID, WorkspaceRole.VIEWER)


def test_should_require_the_editor_role_to_save_a_thumbnail(
    signed_in: TestClient, authorize: AsyncMock
) -> None:
    signed_in.put(f"/diagrams/{DIAGRAM_ID}/thumbnail", headers=AUTH, json={"version": VERSION})

    params = authorize.execute.await_args.args[0]
    assert (params.diagram_id, params.required_role) == (DIAGRAM_ID, WorkspaceRole.EDITOR)


def test_should_forbid_viewers_from_saving_a_thumbnail(
    signed_in: TestClient, authorize: AsyncMock, saving: AsyncMock
) -> None:
    authorize.execute.side_effect = ForbiddenError("This action requires the editor role")

    response = signed_in.put(
        f"/diagrams/{DIAGRAM_ID}/thumbnail", headers=AUTH, json={"version": VERSION}
    )

    assert response.status_code == 403
    saving.execute.assert_not_awaited()
