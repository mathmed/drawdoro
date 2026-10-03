import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.entities.models.folder import Folder
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.folder.get_folder import GetFolder, GetFolderParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(FolderRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> GetFolder:
    return GetFolder(repo)


async def test_should_return_the_folder_when_found(
    sut: GetFolder, repo: NonCallableMagicMock
) -> None:
    folder_id = uuid.uuid4()
    expected = Folder(id=folder_id, project_id=uuid.uuid4(), name="F")
    repo.get_by_id.return_value = expected
    assert await sut.execute(GetFolderParams(folder_id=folder_id)) is expected
    repo.get_by_id.assert_awaited_once_with(folder_id)


async def test_should_raise_not_found_error_when_the_folder_is_missing(
    sut: GetFolder, repo: NonCallableMagicMock
) -> None:
    folder_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Folder {folder_id} not found"):
        await sut.execute(GetFolderParams(folder_id=folder_id))
