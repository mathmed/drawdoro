import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

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

USER_ID = uuid.uuid4()
WORKSPACE_ID = uuid.uuid4()
PROJECT = Project(workspace_id=WORKSPACE_ID, name="P")
DIAGRAM = Diagram(project_id=PROJECT.id, name="D")
FOLDER = Folder(project_id=PROJECT.id, name="F")


@pytest.fixture
def members() -> WorkspaceMemberRepository:
    mock = cast(WorkspaceMemberRepository, create_autospec(WorkspaceMemberRepository))
    mock.get = AsyncMock(  # type: ignore[method-assign]
        return_value=WorkspaceMember(
            workspace_id=WORKSPACE_ID, user_id=USER_ID, role=WorkspaceRole.EDITOR
        )
    )
    return mock


@pytest.fixture
def sut(members: WorkspaceMemberRepository) -> AuthorizeWorkspaceAccess:
    projects = cast(ProjectRepository, create_autospec(ProjectRepository))
    projects.get_by_id = AsyncMock(side_effect=lambda pid: PROJECT if pid == PROJECT.id else None)  # type: ignore[method-assign]
    folders = cast(FolderRepository, create_autospec(FolderRepository))
    folders.get_by_id = AsyncMock(side_effect=lambda fid: FOLDER if fid == FOLDER.id else None)  # type: ignore[method-assign]
    diagrams = cast(DiagramRepository, create_autospec(DiagramRepository))
    diagrams.get_by_id = AsyncMock(side_effect=lambda did: DIAGRAM if did == DIAGRAM.id else None)  # type: ignore[method-assign]
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
    ],
)
async def test_should_allow_members_on_resources_of_their_workspace(
    sut: AuthorizeWorkspaceAccess, members: WorkspaceMemberRepository, ids: dict[str, uuid.UUID]
) -> None:
    member = await sut.execute(params(ids))
    assert member is not None
    members.get.assert_awaited_with(WORKSPACE_ID, USER_ID)  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "ids",
    [
        {"workspace_id": uuid.uuid4(), "project_id": PROJECT.id},
        {"project_id": uuid.uuid4(), "diagram_id": DIAGRAM.id},
        {"project_id": uuid.uuid4(), "folder_id": FOLDER.id},
        {"diagram_id": uuid.uuid4()},
        {"project_id": uuid.uuid4()},
    ],
)
async def test_should_hide_resources_outside_the_given_parents(
    sut: AuthorizeWorkspaceAccess, ids: dict[str, uuid.UUID]
) -> None:
    with pytest.raises(NotFoundError):
        await sut.execute(params(ids))


async def test_should_hide_workspaces_of_non_members(
    sut: AuthorizeWorkspaceAccess, members: WorkspaceMemberRepository
) -> None:
    members.get = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        await sut.execute(params({"workspace_id": WORKSPACE_ID}))


async def test_should_forbid_actions_above_the_member_role(sut: AuthorizeWorkspaceAccess) -> None:
    with pytest.raises(ForbiddenError):
        await sut.execute(params({"workspace_id": WORKSPACE_ID}, WorkspaceRole.OWNER))


def test_should_order_roles() -> None:
    assert WorkspaceRole.OWNER.includes(WorkspaceRole.EDITOR)
    assert WorkspaceRole.EDITOR.includes(WorkspaceRole.VIEWER)
    assert not WorkspaceRole.VIEWER.includes(WorkspaceRole.EDITOR)
