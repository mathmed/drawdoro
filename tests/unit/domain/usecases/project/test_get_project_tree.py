import uuid
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.folder_repository import FolderRepository
from app.domain.entities.models.diagram_summary import DiagramSummary
from app.domain.entities.models.folder import Folder
from app.domain.usecases.project.get_project_tree import GetProjectTree, GetProjectTreeParams

PROJECT_ID = uuid.uuid4()
NOW = datetime.now(UTC)


@pytest.fixture
def folders() -> FolderRepository:
    return cast(FolderRepository, create_autospec(FolderRepository))


@pytest.fixture
def diagrams() -> DiagramRepository:
    return cast(DiagramRepository, create_autospec(DiagramRepository))


@pytest.fixture
def sut(folders: FolderRepository, diagrams: DiagramRepository) -> GetProjectTree:
    return GetProjectTree(folders, diagrams)


async def test_should_return_folders_and_diagram_summaries_of_the_project(
    sut: GetProjectTree, folders: FolderRepository, diagrams: DiagramRepository
) -> None:
    folder = Folder(project_id=PROJECT_ID, name="Services")
    summary = DiagramSummary(
        id=uuid.uuid4(),
        project_id=PROJECT_ID,
        folder_id=folder.id,
        name="Payments",
        created_at=NOW,
        updated_at=NOW,
    )
    folders.list_by_project = AsyncMock(return_value=[folder])  # type: ignore[method-assign]
    diagrams.list_by_project = AsyncMock(return_value=[summary])  # type: ignore[method-assign]

    tree = await sut.execute(GetProjectTreeParams(project_id=PROJECT_ID))

    assert (tree.folders, tree.diagrams) == ([folder], [summary])
    folders.list_by_project.assert_awaited_once_with(PROJECT_ID)
    diagrams.list_by_project.assert_awaited_once_with(PROJECT_ID)


async def test_should_return_empty_tree_for_empty_project(
    sut: GetProjectTree, folders: FolderRepository, diagrams: DiagramRepository
) -> None:
    folders.list_by_project = AsyncMock(return_value=[])  # type: ignore[method-assign]
    diagrams.list_by_project = AsyncMock(return_value=[])  # type: ignore[method-assign]

    tree = await sut.execute(GetProjectTreeParams(project_id=PROJECT_ID))

    assert (tree.folders, tree.diagrams) == ([], [])
