import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.entities.models.folder import Folder
from app.domain.usecases.folder.list_folders import ListFolders, ListFoldersParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(FolderRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ListFolders:
    return ListFolders(repo)


async def test_should_list_the_folders_of_the_project(
    sut: ListFolders, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    folders = [Folder(project_id=project_id, name="Docs")]
    repo.list_by_project.return_value = folders
    assert await sut.execute(ListFoldersParams(project_id=project_id)) == folders
    repo.list_by_project.assert_awaited_once_with(project_id)
