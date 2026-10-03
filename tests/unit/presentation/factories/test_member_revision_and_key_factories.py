from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.api_key.create_api_key import CreateApiKey
from app.domain.usecases.api_key.list_api_keys import ListApiKeys
from app.domain.usecases.api_key.revoke_api_key import RevokeApiKey
from app.domain.usecases.project.get_project_tree import GetProjectTree
from app.domain.usecases.revision.get_diagram_revision import GetDiagramRevision
from app.domain.usecases.revision.list_diagram_revisions import ListDiagramRevisions
from app.domain.usecases.revision.restore_diagram_revision import RestoreDiagramRevision
from app.domain.usecases.workspace_member.add_workspace_member import AddWorkspaceMember
from app.domain.usecases.workspace_member.list_workspace_members import ListWorkspaceMembers
from app.domain.usecases.workspace_member.remove_workspace_member import RemoveWorkspaceMember
from app.domain.usecases.workspace_member.update_workspace_member_role import (
    UpdateWorkspaceMemberRole,
)
from app.presentation.factories.api_key_factories import (
    create_api_key_factory,
    list_api_keys_factory,
    revoke_api_key_factory,
)
from app.presentation.factories.project_factories import get_project_tree_factory
from app.presentation.factories.revision_factories import (
    get_diagram_revision_factory,
    list_diagram_revisions_factory,
    restore_diagram_revision_factory,
)
from app.presentation.factories.workspace_member_factories import (
    add_workspace_member_factory,
    list_workspace_members_factory,
    remove_workspace_member_factory,
    update_workspace_member_role_factory,
)


async def test_should_build_the_workspace_member_use_cases() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await list_workspace_members_factory(session), ListWorkspaceMembers)
    assert isinstance(await add_workspace_member_factory(session), AddWorkspaceMember)
    assert isinstance(
        await update_workspace_member_role_factory(session), UpdateWorkspaceMemberRole
    )
    assert isinstance(await remove_workspace_member_factory(session), RemoveWorkspaceMember)


async def test_should_build_the_revision_use_cases() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await list_diagram_revisions_factory(session), ListDiagramRevisions)
    assert isinstance(await get_diagram_revision_factory(session), GetDiagramRevision)
    assert isinstance(await restore_diagram_revision_factory(session), RestoreDiagramRevision)


async def test_should_build_the_api_key_use_cases() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_api_key_factory(session), CreateApiKey)
    assert isinstance(await list_api_keys_factory(session), ListApiKeys)
    assert isinstance(await revoke_api_key_factory(session), RevokeApiKey)


async def test_should_build_the_project_tree_use_case() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await get_project_tree_factory(session), GetProjectTree)
