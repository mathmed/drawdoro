from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.settings import Settings
from app.domain.usecases.comment.create_comment import CreateComment
from app.domain.usecases.comment.delete_comment import DeleteComment
from app.domain.usecases.comment.list_comments import ListComments
from app.domain.usecases.comment.update_comment_resolution import UpdateCommentResolution
from app.domain.usecases.diagram.create_diagram import CreateDiagram
from app.domain.usecases.diagram.delete_diagram import DeleteDiagram
from app.domain.usecases.diagram.get_diagram import GetDiagram
from app.domain.usecases.diagram.get_diagram_by_share_token import GetDiagramByShareToken
from app.domain.usecases.diagram.list_diagrams import ListDiagrams
from app.domain.usecases.diagram.share_diagram import ShareDiagram
from app.domain.usecases.diagram.update_diagram import UpdateDiagram
from app.domain.usecases.documentation.get_documentation_page import GetDocumentationPage
from app.domain.usecases.documentation.upsert_documentation_page import UpsertDocumentationPage
from app.domain.usecases.folder.create_folder import CreateFolder
from app.domain.usecases.folder.delete_folder import DeleteFolder
from app.domain.usecases.folder.get_folder import GetFolder
from app.domain.usecases.folder.list_folders import ListFolders
from app.domain.usecases.folder.update_folder import UpdateFolder
from app.domain.usecases.gallery.create_gallery_item import CreateGalleryItem
from app.domain.usecases.gallery.delete_gallery_item import DeleteGalleryItem
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem
from app.domain.usecases.gallery.list_gallery_items import ListGalleryItems
from app.domain.usecases.gallery.rename_gallery_item import RenameGalleryItem
from app.domain.usecases.health.check_readiness import CheckReadiness
from app.domain.usecases.project.create_project import CreateProject
from app.domain.usecases.project.delete_project import DeleteProject
from app.domain.usecases.project.get_project import GetProject
from app.domain.usecases.project.list_projects import ListProjects
from app.domain.usecases.project.update_project import UpdateProject
from app.domain.usecases.workspace.create_workspace import CreateWorkspace
from app.domain.usecases.workspace.delete_workspace import DeleteWorkspace
from app.domain.usecases.workspace.get_workspace import GetWorkspace
from app.domain.usecases.workspace.list_workspaces import ListWorkspaces
from app.domain.usecases.workspace.update_workspace import UpdateWorkspace
from app.presentation.factories.comment_factories import (
    create_comment_factory,
    delete_comment_factory,
    list_comments_factory,
    update_comment_resolution_factory,
)
from app.presentation.factories.diagram_factories import (
    create_diagram_factory,
    delete_diagram_factory,
    get_diagram_by_share_token_factory,
    get_diagram_factory,
    list_diagrams_factory,
    share_diagram_factory,
    update_diagram_factory,
)
from app.presentation.factories.documentation_factories import (
    get_documentation_page_factory,
    upsert_documentation_page_factory,
)
from app.presentation.factories.folder_factories import (
    create_folder_factory,
    delete_folder_factory,
    get_folder_factory,
    list_folders_factory,
    update_folder_factory,
)
from app.presentation.factories.gallery_factories import (
    create_gallery_item_factory,
    delete_gallery_item_factory,
    get_gallery_item_factory,
    list_gallery_items_factory,
    rename_gallery_item_factory,
)
from app.presentation.factories.health_factories import check_readiness_factory
from app.presentation.factories.project_factories import (
    create_project_factory,
    delete_project_factory,
    get_project_factory,
    list_projects_factory,
    update_project_factory,
)
from app.presentation.factories.workspace_factories import (
    create_workspace_factory,
    delete_workspace_factory,
    get_workspace_factory,
    list_workspaces_factory,
    update_workspace_factory,
)


async def test_workspace_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_workspace_factory(session), CreateWorkspace)
    assert isinstance(await get_workspace_factory(session), GetWorkspace)
    assert isinstance(await list_workspaces_factory(session), ListWorkspaces)
    assert isinstance(await update_workspace_factory(session), UpdateWorkspace)
    assert isinstance(await delete_workspace_factory(session), DeleteWorkspace)


async def test_project_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_project_factory(session), CreateProject)
    assert isinstance(await get_project_factory(session), GetProject)
    assert isinstance(await list_projects_factory(session), ListProjects)
    assert isinstance(await update_project_factory(session), UpdateProject)
    assert isinstance(await delete_project_factory(session), DeleteProject)


async def test_folder_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_folder_factory(session), CreateFolder)
    assert isinstance(await get_folder_factory(session), GetFolder)
    assert isinstance(await list_folders_factory(session), ListFolders)
    assert isinstance(await update_folder_factory(session), UpdateFolder)
    assert isinstance(await delete_folder_factory(session), DeleteFolder)


async def test_diagram_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_diagram_factory(session), CreateDiagram)
    assert isinstance(await get_diagram_factory(session), GetDiagram)
    assert isinstance(await list_diagrams_factory(session), ListDiagrams)
    assert isinstance(await update_diagram_factory(session), UpdateDiagram)
    assert isinstance(await delete_diagram_factory(session), DeleteDiagram)
    assert isinstance(await share_diagram_factory(session), ShareDiagram)
    assert isinstance(await get_diagram_by_share_token_factory(session), GetDiagramByShareToken)


async def test_comment_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_comment_factory(session), CreateComment)
    assert isinstance(await list_comments_factory(session), ListComments)
    assert isinstance(await delete_comment_factory(session), DeleteComment)
    assert isinstance(await update_comment_resolution_factory(session), UpdateCommentResolution)


async def test_documentation_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await get_documentation_page_factory(session), GetDocumentationPage)
    assert isinstance(await upsert_documentation_page_factory(session), UpsertDocumentationPage)


async def test_gallery_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await create_gallery_item_factory(session, Settings()), CreateGalleryItem)
    assert isinstance(await list_gallery_items_factory(session), ListGalleryItems)
    assert isinstance(await get_gallery_item_factory(session), GetGalleryItem)
    assert isinstance(await rename_gallery_item_factory(session), RenameGalleryItem)
    assert isinstance(await delete_gallery_item_factory(session), DeleteGalleryItem)


async def test_health_factories() -> None:
    session = MagicMock(spec=AsyncSession)
    assert isinstance(await check_readiness_factory(session), CheckReadiness)
