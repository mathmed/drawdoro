import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.diagram import Diagram
from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project import Project
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.usecases.auth.authorize_workspace_access import (
    AuthorizeWorkspaceAccess,
    AuthorizeWorkspaceAccessParams,
)
from tests.doubles import double

USER_ID = uuid.uuid4()
WORKSPACE_ID = uuid.uuid4()
PROJECT = Project(workspace_id=WORKSPACE_ID, name="P")
DIAGRAM = Diagram(project_id=PROJECT.id, name="D")
FOLDER = Folder(project_id=PROJECT.id, name="F")


@pytest.fixture
def members() -> NonCallableMagicMock:
    mock = double(WorkspaceMemberRepository)
    mock.get.return_value = WorkspaceMember(
        workspace_id=WORKSPACE_ID, user_id=USER_ID, role=WorkspaceRole.EDITOR
    )
    return mock


@pytest.fixture
def sut(members: NonCallableMagicMock) -> AuthorizeWorkspaceAccess:
    projects = double(ProjectRepository)
    projects.get_by_id.side_effect = lambda pid: PROJECT if pid == PROJECT.id else None
    folders = double(FolderRepository)
    folders.get_by_id.side_effect = lambda fid: FOLDER if fid == FOLDER.id else None
    diagrams = double(DiagramRepository)
    diagrams.get_by_id.side_effect = lambda did: DIAGRAM if did == DIAGRAM.id else None
    return AuthorizeWorkspaceAccess(members, projects, folders, diagrams)


def params(
    ids: dict[str, uuid.UUID] | None = None, role: WorkspaceRole = WorkspaceRole.VIEWER
) -> AuthorizeWorkspaceAccessParams:
    return AuthorizeWorkspaceAccessParams.model_validate(
        {"user_id": USER_ID, "required_role": role, **(ids or {})}
    )


async def test_should_skip_requests_without_resource(sut: AuthorizeWorkspaceAccess) -> None:
    assert await sut.execute(params()) is None


@pytest.mark.parametrize(
    "ids",
    [
        {"workspace_id": WORKSPACE_ID},
        {"project_id": PROJECT.id},
        {"workspace_id": WORKSPACE_ID, "project_id": PROJECT.id},
        {"project_id": PROJECT.id, "diagram_id": DIAGRAM.id},
        {"diagram_id": DIAGRAM.id},
        {"project_id": PROJECT.id, "folder_id": FOLDER.id},
        {"folder_id": FOLDER.id},
    ],
)
async def test_should_allow_members_on_resources_of_their_workspace(
    sut: AuthorizeWorkspaceAccess, members: NonCallableMagicMock, ids: dict[str, uuid.UUID]
) -> None:
    member = await sut.execute(params(ids))
    assert member is not None
    members.get.assert_awaited_with(WORKSPACE_ID, USER_ID)


@pytest.mark.parametrize(
    ("ids", "message"),
    [
        ({"workspace_id": uuid.uuid4(), "project_id": PROJECT.id}, "Project not found"),
        ({"project_id": uuid.uuid4(), "diagram_id": DIAGRAM.id}, "Diagram not found"),
        ({"project_id": uuid.uuid4(), "folder_id": FOLDER.id}, "Folder not found"),
        ({"diagram_id": uuid.uuid4()}, "Diagram not found"),
        ({"folder_id": uuid.uuid4()}, "Folder not found"),
        ({"project_id": uuid.uuid4()}, "Project not found"),
    ],
)
async def test_should_hide_resources_outside_the_given_parents(
    sut: AuthorizeWorkspaceAccess, ids: dict[str, uuid.UUID], message: str
) -> None:
    with pytest.raises(NotFoundError, match=f"^{message}$"):
        await sut.execute(params(ids))


async def test_should_hide_workspaces_of_non_members(
    sut: AuthorizeWorkspaceAccess, members: NonCallableMagicMock
) -> None:
    members.get.return_value = None
    with pytest.raises(NotFoundError, match="^Workspace not found$"):
        await sut.execute(params({"workspace_id": WORKSPACE_ID}))


async def test_should_forbid_actions_above_the_member_role(sut: AuthorizeWorkspaceAccess) -> None:
    with pytest.raises(ForbiddenError, match="^This action requires the owner role$"):
        await sut.execute(params({"workspace_id": WORKSPACE_ID}, WorkspaceRole.OWNER))


def test_should_order_roles() -> None:
    assert WorkspaceRole.OWNER.includes(WorkspaceRole.EDITOR)
    assert WorkspaceRole.EDITOR.includes(WorkspaceRole.VIEWER)
    assert not WorkspaceRole.VIEWER.includes(WorkspaceRole.EDITOR)
