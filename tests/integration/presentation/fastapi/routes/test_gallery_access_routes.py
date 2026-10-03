import uuid
from collections.abc import Callable, Iterator
from typing import Any
from unittest.mock import AsyncMock, NonCallableMagicMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.diagram_revision_repository import DiagramRevisionRepository
from app.domain.contracts.diagram_update_notifier import DiagramUpdateNotifier
from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.gallery_item_repository import GalleryItemRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.api_key_owner import ApiKeyOwner
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.entities.models.project import Project
from app.domain.entities.models.user import User
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.entities.objects.gallery_limits import GalleryLimits
from app.domain.entities.objects.revision_policy import RevisionPolicy
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.services.revision_recorder import RevisionRecorder
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem
from app.domain.usecases.gallery.insert_gallery_item import InsertGalleryItem
from app.domain.usecases.gallery.list_gallery_items import ListGalleryItems
from app.domain.usecases.gallery.update_gallery_item import UpdateGalleryItem
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_api_key_factory,
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.gallery_factories import (
    get_gallery_item_factory,
    insert_gallery_item_factory,
    list_gallery_items_factory,
    update_gallery_item_factory,
)
from app.presentation.factories.presence_factories import track_agent_activity_factory
from app.presentation.fastapi.dependencies.gallery_owner import PERSONAL_GALLERY_ONLY
from tests.doubles import double
from tests.tldraw_records import binding, canvas, content, geo, group, png, saved_canvas

ANA = User(email="ana@example.com", name="Ana")
BRUNO = User(email="bruno@example.com", name="Bruno")
ANAS_KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_laptop", key_hash="h1")
WORKSPACE_ID = uuid.uuid4()
PROJECT = Project(workspace_id=WORKSPACE_ID, name="Shop")
# A diagram in a workspace Ana is not a member of.
FOREIGN_PROJECT = Project(workspace_id=uuid.uuid4(), name="Elsewhere")

SESSION = {"Authorization": "Bearer ana"}
AGENT = {"X-API-Key": "mcpk_laptop_secret", "X-Agent-Name": "Claude"}
SERVICE = {"X-API-Key": "service-secret", "X-Agent-Name": "Claude"}
REVOKED = {"X-API-Key": "mcpk_revoked_secret", "X-Agent-Name": "Claude"}


class InMemoryGallery(GalleryItemRepository):
    def __init__(self, *items: GalleryItem) -> None:
        self.rows = {item.id: item for item in items}

    async def create(self, item: GalleryItem) -> GalleryItem:
        self.rows[item.id] = item
        return item

    async def get_by_id(self, item_id: uuid.UUID) -> GalleryItem | None:
        return self.rows.get(item_id)

    async def list_by_owner(
        self, owner_id: uuid.UUID | None, include_thumbnails: bool = True
    ) -> list[GalleryItemSummary]:
        return [
            GalleryItemSummary.model_validate(item.model_dump(exclude={"content", "image_data"}))
            for item in self.rows.values()
            if item.owner_id == owner_id
        ]

    async def update_details(self, item: GalleryItemSummary) -> GalleryItemSummary:
        stored = self.rows[item.id]
        self.rows[item.id] = stored.model_copy(
            update={"name": item.name, "tags": item.tags, "description": item.description}
        )
        return item

    async def delete(self, item_id: uuid.UUID) -> None:
        self.rows.pop(item_id, None)


def shapes_item(owner: User, name: str = "Queue") -> GalleryItem:
    saved = content(
        [
            group("shape:g", 0, 0),
            geo("shape:a", 0, 0, 100, 50, parent="shape:g", index="a1"),
            geo("shape:b", 300, 0, 100, 50, parent="shape:g", index="a2"),
        ],
        bindings=[binding("binding:x", "shape:a", "shape:b", "end")],
    )
    return GalleryItem(
        owner_id=owner.id, name=name, kind=GalleryItemKind.SHAPES, tags=["queue"], content=saved
    )


ANAS_ITEM = shapes_item(ANA)
ANAS_IMAGE = GalleryItem(
    owner_id=ANA.id,
    name="Logo",
    kind=GalleryItemKind.IMAGE,
    image_data=png(40, 20),
    image_mime_type=ImageMimeType.PNG,
)
BRUNOS_ITEM = shapes_item(BRUNO, "Secret")


async def authenticate_key(params: AuthenticateApiKeyParams) -> ApiKeyOwner:
    if params.secret != "mcpk_laptop_secret":
        raise UnauthorizedError("Invalid or revoked API key")
    return ApiKeyOwner(api_key=ANAS_KEY, user=ANA)


@pytest.fixture
def role() -> WorkspaceRole:
    return WorkspaceRole.EDITOR


@pytest.fixture
def diagram() -> Diagram:
    return Diagram(project_id=PROJECT.id, name="Checkout", canvas_state=canvas(geo("shape:api")))


@pytest.fixture
def foreign_diagram() -> Diagram:
    return Diagram(project_id=FOREIGN_PROJECT.id, name="Secret", canvas_state=canvas())


@pytest.fixture
def notifier() -> AsyncMock:
    return AsyncMock(spec=DiagramUpdateNotifier)


@pytest.fixture
def revisions() -> NonCallableMagicMock:
    mock = double(DiagramRevisionRepository)
    mock.get_latest.return_value = None
    mock.create.side_effect = lambda revision: revision
    return mock


@pytest.fixture
def client(
    role: WorkspaceRole,
    diagram: Diagram,
    foreign_diagram: Diagram,
    notifier: AsyncMock,
    revisions: NonCallableMagicMock,
) -> Iterator[TestClient]:
    gallery = InMemoryGallery(ANAS_ITEM, ANAS_IMAGE, BRUNOS_ITEM)
    diagrams = AsyncMock(spec=DiagramRepository)
    by_id = {diagram.id: diagram, foreign_diagram.id: foreign_diagram}
    diagrams.get_by_id.side_effect = by_id.get
    diagrams.update.side_effect = lambda updated: updated
    projects = AsyncMock(spec=ProjectRepository)
    projects.get_by_id.side_effect = {PROJECT.id: PROJECT, FOREIGN_PROJECT.id: FOREIGN_PROJECT}.get
    members = AsyncMock(spec=WorkspaceMemberRepository)
    member = WorkspaceMember(workspace_id=WORKSPACE_ID, user_id=ANA.id, role=role)
    members.get.side_effect = lambda workspace_id, _: (
        member if workspace_id == WORKSPACE_ID else None
    )
    authorize = AuthorizeWorkspaceAccess(
        members, projects, AsyncMock(spec=FolderRepository), diagrams
    )
    authenticate = AsyncMock(spec=AuthenticateUser)
    authenticate.execute.return_value = ANA
    keys = AsyncMock(spec=AuthenticateApiKey)
    keys.execute.side_effect = authenticate_key
    recorder = RevisionRecorder(revisions, RevisionPolicy())
    limits = GalleryLimits(max_image_bytes=1_000_000, max_shapes_bytes=1_000_000)
    overrides: dict[Callable[..., Any], Callable[[], object]] = {
        get_settings: lambda: Settings(auth_enabled=True, service_api_key="service-secret"),
        authenticate_user_factory: lambda: authenticate,
        authenticate_api_key_factory: lambda: keys,
        authorize_workspace_access_factory: lambda: authorize,
        track_agent_activity_factory: lambda: AsyncMock(),
        list_gallery_items_factory: lambda: ListGalleryItems(gallery),
        get_gallery_item_factory: lambda: GetGalleryItem(gallery),
        update_gallery_item_factory: lambda: UpdateGalleryItem(gallery),
        insert_gallery_item_factory: lambda: InsertGalleryItem(
            gallery, diagrams, notifier, recorder, limits
        ),
    }
    app.dependency_overrides.update(overrides)
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def insert(client: TestClient, diagram: Diagram, headers: dict[str, str], **body: Any) -> Any:
    payload = {"item_id": str(ANAS_ITEM.id)} | body
    return client.post(f"/diagrams/{diagram.id}/gallery-insertions", headers=headers, json=payload)


@pytest.mark.parametrize("headers", [SESSION, AGENT])
def test_should_list_only_the_callers_items(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get("/gallery", headers=headers)

    assert response.status_code == 200
    assert {item["name"] for item in response.json()} == {"Queue", "Logo"}


def test_should_search_the_callers_items_by_tag(client: TestClient) -> None:
    response = client.get("/gallery", headers=AGENT, params={"tag": "queue"})
    assert [item["name"] for item in response.json()] == ["Queue"]


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/gallery"),
        ("GET", f"/gallery/{ANAS_ITEM.id}"),
        ("PATCH", f"/gallery/{ANAS_ITEM.id}"),
        ("DELETE", f"/gallery/{ANAS_ITEM.id}"),
        ("POST", "/gallery"),
    ],
)
def test_should_explain_that_the_service_key_has_no_gallery(
    client: TestClient, method: str, path: str
) -> None:
    body = (
        {"name": "x", "kind": "shapes", "content": {"shapes": [{}]}} if method == "POST" else None
    )
    if method == "PATCH":
        body = {"name": "x"}

    response = client.request(method, path, headers=SERVICE, json=body)

    assert response.status_code == 403
    assert response.json()["detail"] == PERSONAL_GALLERY_ONLY


def test_should_reject_a_revoked_key(client: TestClient, diagram: Diagram) -> None:
    assert client.get("/gallery", headers=REVOKED).status_code == 401
    assert insert(client, diagram, REVOKED).status_code == 401


def test_should_hide_items_of_other_people(client: TestClient, diagram: Diagram) -> None:
    assert client.get(f"/gallery/{BRUNOS_ITEM.id}", headers=AGENT).status_code == 404
    assert (
        client.patch(f"/gallery/{BRUNOS_ITEM.id}", headers=AGENT, json={"tags": ["x"]}).status_code
        == 404
    )
    response = insert(client, diagram, AGENT, item_id=str(BRUNOS_ITEM.id))
    assert response.status_code == 404
    assert response.json()["detail"] == f"Gallery item {BRUNOS_ITEM.id} not found"


def test_should_report_a_missing_item(client: TestClient, diagram: Diagram) -> None:
    missing = uuid.uuid4()
    response = insert(client, diagram, AGENT, item_id=str(missing))
    assert response.status_code == 404
    assert str(missing) in response.json()["detail"]


def test_should_let_the_agent_tag_its_owners_items(client: TestClient) -> None:
    response = client.patch(
        f"/gallery/{ANAS_ITEM.id}",
        headers=AGENT,
        json={"tags": ["Queue", "Kafka"], "description": "Topic and consumers"},
    )

    assert response.status_code == 200
    assert (response.json()["tags"], response.json()["description"]) == (
        ["queue", "kafka"],
        "Topic and consumers",
    )


def test_should_insert_into_a_diagram_as_the_owners_agent(
    client: TestClient,
    diagram: Diagram,
    notifier: AsyncMock,
    revisions: NonCallableMagicMock,
) -> None:
    response = insert(client, diagram, AGENT, near_shape_id="shape:api", side="below", gap=40)

    assert response.status_code == 201
    body = response.json()
    assert (body["diagram_id"], body["item_id"]) == (str(diagram.id), str(ANAS_ITEM.id))
    assert len(body["created_ids"]) == 4
    assert len(body["root_shape_ids"]) == 1
    assert (body["x"], body["y"], body["width"], body["height"]) == (0, 90, 400, 50)
    assert "canvas_state" not in body
    store = saved_canvas(diagram)["store"]
    assert set(body["created_ids"]) <= set(store)
    revision = revisions.create.await_args.args[0]
    assert (revision.origin, revision.author_id, revision.agent_name, revision.agent_label) == (
        RevisionOrigin.AGENT,
        ANA.id,
        "Claude",
        "laptop",
    )
    assert revision.summary == "Inserted “Queue” from the gallery"
    notifier.notify_updated.assert_awaited_once()


def test_should_insert_an_image(client: TestClient, diagram: Diagram) -> None:
    response = insert(client, diagram, SESSION, item_id=str(ANAS_IMAGE.id), x=10, y=20, scale=2)

    assert response.status_code == 201
    assert (response.json()["width"], response.json()["height"]) == (80, 40)
    store = saved_canvas(diagram)["store"]
    asset = next(store[i] for i in response.json()["created_ids"] if i.startswith("asset:"))
    assert asset["props"]["src"].startswith("data:image/png;base64,")


def test_should_not_let_the_service_key_insert(client: TestClient, diagram: Diagram) -> None:
    response = insert(client, diagram, SERVICE)

    assert response.status_code == 403
    assert response.json()["detail"] == PERSONAL_GALLERY_ONLY


@pytest.mark.parametrize("role", [WorkspaceRole.VIEWER])
def test_should_need_the_editor_role_in_the_diagrams_workspace(
    client: TestClient, diagram: Diagram, notifier: AsyncMock
) -> None:
    response = insert(client, diagram, AGENT)

    assert response.status_code == 403
    assert "editor" in response.json()["detail"]
    notifier.notify_updated.assert_not_awaited()


def test_should_hide_diagrams_of_other_workspaces(
    client: TestClient, foreign_diagram: Diagram
) -> None:
    response = insert(client, foreign_diagram, AGENT)

    assert response.status_code == 404
    assert foreign_diagram.canvas_state == canvas()


@pytest.mark.parametrize(
    "body",
    [
        {"scale": 0},
        {"scale": -1},
        {"gap": -1},
        {"side": "diagonal"},
        {"item_id": "nope"},
        {"revision_summary": "x" * 501},
    ],
)
def test_should_validate_the_insertion_request(
    client: TestClient, diagram: Diagram, body: dict[str, Any]
) -> None:
    assert insert(client, diagram, AGENT, **body).status_code == 422


# Python's JSON parser reads NaN and Infinity, which a canvas can't store, so the body is raw text.
@pytest.mark.parametrize(
    "numbers",
    ['"x": NaN, "y": 0', '"x": 0, "y": Infinity', '"x": -Infinity, "y": 0', '"x": 1e10, "y": 0'],
)
def test_should_refuse_coordinates_a_canvas_cannot_hold(
    client: TestClient, diagram: Diagram, notifier: AsyncMock, numbers: str
) -> None:
    response = client.post(
        f"/diagrams/{diagram.id}/gallery-insertions",
        headers=AGENT | {"Content-Type": "application/json"},
        content=f'{{"item_id": "{ANAS_ITEM.id}", {numbers}}}',
    )

    assert response.status_code == 422
    notifier.notify_updated.assert_not_awaited()


def test_should_accept_coordinates_far_from_the_origin(
    client: TestClient, diagram: Diagram
) -> None:
    response = insert(client, diagram, AGENT, x=-1e9, y=1e9)

    assert response.status_code == 201
    assert (response.json()["x"], response.json()["y"]) == (-1e9, 1e9)


def test_should_explain_why_an_insertion_is_refused(client: TestClient, diagram: Diagram) -> None:
    response = insert(client, diagram, AGENT, x=1, near_shape_id="shape:api")

    assert response.status_code == 422
    assert response.json()["detail"] == "Pass either x and y or near_shape_id, not both"
