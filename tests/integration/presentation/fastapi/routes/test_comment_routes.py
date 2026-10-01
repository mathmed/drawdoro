import uuid
from collections.abc import Callable, Iterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.common.settings import Settings, get_settings
from app.domain.contracts.comment_change_notifier import CommentChangeNotifier
from app.domain.contracts.comment_repository import CommentRepository
from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.api_key_owner import ApiKeyOwner
from app.domain.entities.models.comment import Comment
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.project import Project
from app.domain.entities.models.user import User
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.comment_status import CommentStatus
from app.domain.enums.revision_origin import RevisionOrigin
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.domain.usecases.comment.create_comment import CreateComment
from app.domain.usecases.comment.delete_comment import DeleteComment
from app.domain.usecases.comment.list_comments import ListComments
from app.domain.usecases.comment.update_comment_resolution import UpdateCommentResolution
from app.main.main import app
from app.presentation.factories.auth_factories import (
    authenticate_api_key_factory,
    authenticate_user_factory,
    authorize_workspace_access_factory,
)
from app.presentation.factories.comment_factories import (
    create_comment_factory,
    delete_comment_factory,
    list_comments_factory,
    update_comment_resolution_factory,
)
from app.presentation.factories.presence_factories import track_agent_activity_factory

ANA = User(email="ana@example.com", name="Ana")
BRUNO = User(email="bruno@example.com", name="Bruno")
ANAS_KEY = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_laptop", key_hash="h1")
ANAS_OTHER_KEY = ApiKey(user_id=ANA.id, label="desktop", prefix="mcpk_desk", key_hash="h2")
WORKSPACE_ID = uuid.uuid4()
PROJECT = Project(workspace_id=WORKSPACE_ID, name="Shop")
DIAGRAM = Diagram(project_id=PROJECT.id, name="Checkout")
# A diagram in a workspace Ana is not a member of.
FOREIGN_PROJECT = Project(workspace_id=uuid.uuid4(), name="Elsewhere")
FOREIGN_DIAGRAM = Diagram(project_id=FOREIGN_PROJECT.id, name="Secret")

SESSION = {"Authorization": "Bearer ana"}
AGENT = {"X-API-Key": "mcpk_laptop_secret", "X-Agent-Name": "Claude"}
OTHER_AGENT = {"X-API-Key": "mcpk_desktop_secret", "X-Agent-Name": "Claude"}
SERVICE = {"X-API-Key": "service-secret", "X-Agent-Name": "Claude"}
REVOKED = {"X-API-Key": "mcpk_revoked_secret", "X-Agent-Name": "Claude"}
BASE = f"/diagrams/{DIAGRAM.id}/comments"


class InMemoryComments(CommentRepository):
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Comment] = {}

    def _named(self, comment: Comment) -> Comment:
        names = {ANA.id: ANA.name, BRUNO.id: BRUNO.name}
        return comment.model_copy(
            update={
                "author_name": names.get(comment.author_id) if comment.author_id else None,
                "resolved_by_name": (
                    names.get(comment.resolved_by_id) if comment.resolved_by_id else None
                ),
            }
        )

    async def create(self, comment: Comment) -> Comment:
        self.rows[comment.id] = comment
        return self._named(comment)

    async def list_by_diagram(
        self, diagram_id: uuid.UUID, status: CommentStatus = CommentStatus.ALL
    ) -> list[Comment]:
        wanted = {
            CommentStatus.ALL: (True, False),
            CommentStatus.OPEN: (False,),
            CommentStatus.RESOLVED: (True,),
        }[status]
        return [
            self._named(c)
            for c in self.rows.values()
            if c.diagram_id == diagram_id and c.is_resolved in wanted
        ]

    async def get(self, diagram_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
        comment = self.rows.get(comment_id)
        if comment is None or comment.diagram_id != diagram_id:
            return None
        return self._named(comment)

    async def update_resolution(self, comment: Comment) -> Comment:
        self.rows[comment.id] = comment
        return self._named(comment)

    async def delete(self, comment_id: uuid.UUID) -> None:
        self.rows.pop(comment_id, None)


async def authenticate_key(params: AuthenticateApiKeyParams) -> ApiKeyOwner:
    keys = {"mcpk_laptop_secret": ANAS_KEY, "mcpk_desktop_secret": ANAS_OTHER_KEY}
    if params.secret not in keys:
        raise UnauthorizedError("Invalid or revoked API key")
    return ApiKeyOwner(api_key=keys[params.secret], user=ANA)


@pytest.fixture
def role() -> WorkspaceRole:
    return WorkspaceRole.EDITOR


@pytest.fixture
def store() -> InMemoryComments:
    return InMemoryComments()


@pytest.fixture
def notifier() -> AsyncMock:
    return AsyncMock(spec=CommentChangeNotifier)


@pytest.fixture
def client(
    role: WorkspaceRole, store: InMemoryComments, notifier: AsyncMock
) -> Iterator[TestClient]:
    diagrams = AsyncMock(spec=DiagramRepository)
    by_id = {DIAGRAM.id: DIAGRAM, FOREIGN_DIAGRAM.id: FOREIGN_DIAGRAM}
    diagrams.get_by_id.side_effect = by_id.get
    diagrams.exists.side_effect = lambda diagram_id: diagram_id in by_id
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
    overrides: dict[Callable[..., Any], Callable[[], object]] = {
        get_settings: lambda: Settings(auth_enabled=True, service_api_key="service-secret"),
        authenticate_user_factory: lambda: authenticate,
        authenticate_api_key_factory: lambda: keys,
        authorize_workspace_access_factory: lambda: authorize,
        track_agent_activity_factory: lambda: AsyncMock(),
        create_comment_factory: lambda: CreateComment(store, diagrams, notifier),
        list_comments_factory: lambda: ListComments(store, diagrams),
        delete_comment_factory: lambda: DeleteComment(store, notifier),
        update_comment_resolution_factory: lambda: UpdateCommentResolution(store, notifier),
    }
    app.dependency_overrides.update(overrides)
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def seed(store: InMemoryComments, **values: object) -> Comment:
    comment = Comment.model_validate(
        {"diagram_id": DIAGRAM.id, "element_id": "shape:a", "content": "Missing X"} | values
    )
    store.rows[comment.id] = comment
    return comment


def test_should_create_a_persons_comment(client: TestClient, notifier: AsyncMock) -> None:
    response = client.post(
        BASE, headers=SESSION, json={"element_id": "shape:a", "content": "Missing <b>X</b>"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "Missing <b>X</b>"
    assert (body["author_id"], body["author_name"], body["origin"]) == (
        str(ANA.id),
        "Ana",
        "human",
    )
    assert (body["resolved"], body["resolved_at"], body["created_by_you"]) == (False, None, True)
    assert "api_key_id" not in body
    notifier.notify_changed.assert_awaited_once_with(DIAGRAM.id)


def test_should_create_an_agents_comment_as_the_key_owners_agent(
    client: TestClient, store: InMemoryComments
) -> None:
    response = client.post(BASE, headers=AGENT, json={"content": "Added the queue"})
    assert response.status_code == 201
    body = response.json()
    assert (body["origin"], body["agent_name"], body["agent_label"]) == (
        "agent",
        "Claude",
        "laptop",
    )
    assert (body["author_id"], body["author_name"], body["element_id"]) == (
        str(ANA.id),
        "Ana",
        None,
    )
    [stored] = store.rows.values()
    assert stored.api_key_id == ANAS_KEY.id


def test_should_create_an_ownerless_agent_comment_with_the_service_key(client: TestClient) -> None:
    body = {"content": "Hi", "author_id": str(BRUNO.id)}
    response = client.post(BASE, headers=SERVICE, json=body)
    assert response.status_code == 201
    assert (response.json()["origin"], response.json()["author_id"]) == ("agent", None)


@pytest.mark.parametrize("content", ["", "   ", "x" * 5001])
def test_should_reject_invalid_text(client: TestClient, content: str) -> None:
    assert client.post(BASE, headers=AGENT, json={"content": content}).status_code == 422


def test_should_list_with_a_status_filter(client: TestClient, store: InMemoryComments) -> None:
    open_one = seed(store)
    resolved = seed(store, resolved_at="2026-09-30T10:00:00Z", resolved_by_id=str(BRUNO.id))
    listed = {
        status: [c["id"] for c in client.get(f"{BASE}?status={status}", headers=AGENT).json()]
        for status in ("open", "resolved", "all")
    }
    assert listed == {
        "open": [str(open_one.id)],
        "resolved": [str(resolved.id)],
        "all": [str(open_one.id), str(resolved.id)],
    }
    assert [c["id"] for c in client.get(BASE, headers=AGENT).json()] == listed["all"]
    assert client.get(f"{BASE}?status=done", headers=AGENT).status_code == 422


def test_should_tell_agents_which_comments_their_key_wrote(
    client: TestClient, store: InMemoryComments
) -> None:
    mine = seed(store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_KEY.id)
    seed(store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_OTHER_KEY.id)
    seed(store, author_id=ANA.id)
    flags = {c["id"]: c["created_by_you"] for c in client.get(BASE, headers=AGENT).json()}
    assert [comment_id for comment_id, own in flags.items() if own] == [str(mine.id)]


def test_should_let_an_agent_resolve_and_reopen_a_persons_comment(
    client: TestClient, store: InMemoryComments, notifier: AsyncMock
) -> None:
    comment = seed(store, author_id=BRUNO.id)
    resolved = client.patch(f"{BASE}/{comment.id}", headers=AGENT, json={"resolved": True})
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["resolved"] is True
    assert body["resolved_at"] is not None
    assert (body["resolved_by_id"], body["resolved_by_name"]) == (str(ANA.id), "Ana")
    assert (body["resolved_by_origin"], body["resolved_by_agent_name"]) == ("agent", "Claude")
    assert body["resolved_by_agent_label"] == "laptop"
    assert body["created_by_you"] is False

    reopened = client.patch(f"{BASE}/{comment.id}", headers=SESSION, json={"resolved": False})
    assert reopened.status_code == 200
    assert (reopened.json()["resolved"], reopened.json()["resolved_by_id"]) == (False, None)
    assert notifier.notify_changed.await_count == 2


def test_should_need_the_resolved_flag(client: TestClient, store: InMemoryComments) -> None:
    comment = seed(store)
    assert client.patch(f"{BASE}/{comment.id}", headers=AGENT, json={}).status_code == 422


def test_should_let_an_agent_delete_only_its_own_comments(
    client: TestClient, store: InMemoryComments
) -> None:
    mine = seed(store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_KEY.id)
    persons = seed(store, author_id=ANA.id)
    other_agents = seed(
        store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_OTHER_KEY.id
    )

    assert client.delete(f"{BASE}/{persons.id}", headers=AGENT).status_code == 403
    denied = client.delete(f"{BASE}/{other_agents.id}", headers=AGENT)
    assert denied.status_code == 403
    assert "Resolve this comment instead" in denied.json()["detail"]
    assert client.delete(f"{BASE}/{mine.id}", headers=AGENT).status_code == 204
    assert set(store.rows) == {persons.id, other_agents.id}


def test_should_not_let_the_service_key_delete_keyed_or_human_comments(
    client: TestClient, store: InMemoryComments
) -> None:
    keyed = seed(store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_KEY.id)
    ownerless = seed(store, origin=RevisionOrigin.AGENT)
    assert client.delete(f"{BASE}/{keyed.id}", headers=SERVICE).status_code == 403
    assert client.delete(f"{BASE}/{ownerless.id}", headers=SERVICE).status_code == 204


def test_should_keep_letting_people_delete_any_comment(
    client: TestClient, store: InMemoryComments
) -> None:
    agents = seed(store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_KEY.id)
    bruno = seed(store, author_id=BRUNO.id)
    assert client.delete(f"{BASE}/{agents.id}", headers=SESSION).status_code == 204
    assert client.delete(f"{BASE}/{bruno.id}", headers=SESSION).status_code == 204
    assert store.rows == {}


@pytest.mark.parametrize("role", [WorkspaceRole.VIEWER])
@pytest.mark.parametrize("headers", [AGENT, SESSION], ids=["agent", "person"])
def test_should_let_viewers_only_read(
    client: TestClient, store: InMemoryComments, headers: dict[str, str]
) -> None:
    mine = seed(store, origin=RevisionOrigin.AGENT, author_id=ANA.id, api_key_id=ANAS_KEY.id)
    assert client.get(BASE, headers=headers).status_code == 200
    assert client.post(BASE, headers=headers, json={"content": "Hi"}).status_code == 403
    patch = client.patch(f"{BASE}/{mine.id}", headers=headers, json={"resolved": True})
    assert patch.status_code == 403
    assert client.delete(f"{BASE}/{mine.id}", headers=headers).status_code == 403
    assert store.rows[mine.id].is_resolved is False
    assert len(store.rows) == 1


def test_should_hide_diagrams_of_other_workspaces(
    client: TestClient, store: InMemoryComments
) -> None:
    foreign = seed(store, diagram_id=FOREIGN_DIAGRAM.id)
    base = f"/diagrams/{FOREIGN_DIAGRAM.id}/comments"
    assert client.get(base, headers=AGENT).status_code == 404
    assert client.post(base, headers=AGENT, json={"content": "Hi"}).status_code == 404
    patch = client.patch(f"{base}/{foreign.id}", headers=AGENT, json={"resolved": True})
    assert patch.status_code == 404
    assert client.delete(f"{base}/{foreign.id}", headers=AGENT).status_code == 404
    assert store.rows[foreign.id].is_resolved is False


def test_should_not_reach_comments_through_another_diagram(
    client: TestClient, store: InMemoryComments
) -> None:
    other_diagram_comment = seed(store, diagram_id=uuid.uuid4(), author_id=ANA.id)
    url = f"{BASE}/{other_diagram_comment.id}"
    assert client.delete(url, headers=SESSION).status_code == 404
    assert client.patch(url, headers=SESSION, json={"resolved": True}).status_code == 404
    assert other_diagram_comment.id in store.rows


def test_should_report_missing_comments(client: TestClient) -> None:
    url = f"{BASE}/{uuid.uuid4()}"
    response = client.patch(url, headers=AGENT, json={"resolved": True})
    assert response.status_code == 404
    assert "not found in this diagram" in response.json()["detail"]
    assert client.delete(url, headers=AGENT).status_code == 404


def test_should_report_missing_diagrams_to_the_service_key(client: TestClient) -> None:
    base = f"/diagrams/{uuid.uuid4()}/comments"
    assert client.get(base, headers=SERVICE).status_code == 404
    assert client.post(base, headers=SERVICE, json={"content": "Hi"}).status_code == 404


def test_should_reject_revoked_keys(client: TestClient, store: InMemoryComments) -> None:
    comment = seed(store)
    assert client.get(BASE, headers=REVOKED).status_code == 401
    assert client.post(BASE, headers=REVOKED, json={"content": "Hi"}).status_code == 401
    patch = client.patch(f"{BASE}/{comment.id}", headers=REVOKED, json={"resolved": True})
    assert patch.status_code == 401
    assert client.delete(f"{BASE}/{comment.id}", headers=REVOKED).status_code == 401
    assert store.rows[comment.id].is_resolved is False
