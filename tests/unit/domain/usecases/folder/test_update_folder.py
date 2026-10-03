import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.entities.models.folder import Folder
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.folder.update_folder import UpdateFolder, UpdateFolderParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(FolderRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> UpdateFolder:
    return UpdateFolder(repo)


async def test_should_update_the_folder_when_found(
    sut: UpdateFolder, repo: NonCallableMagicMock
) -> None:
    folder_id = uuid.uuid4()
    parent_folder_id = uuid.uuid4()
    repo.get_by_id.return_value = Folder(id=folder_id, project_id=uuid.uuid4(), name="Old")
    repo.update.side_effect = lambda folder: folder
    result = await sut.execute(
        UpdateFolderParams(folder_id=folder_id, name="New", parent_folder_id=parent_folder_id)
    )
    repo.get_by_id.assert_awaited_once_with(folder_id)
    updated = repo.update.await_args.args[0]
    assert result is updated
    assert updated.id == folder_id
    assert updated.name == "New"
    assert updated.parent_folder_id == parent_folder_id


async def test_should_raise_not_found_error_when_the_folder_is_missing(
    sut: UpdateFolder, repo: NonCallableMagicMock
) -> None:
    folder_id = uuid.uuid4()
    parent_folder_id = uuid.uuid4()
    repo.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"Folder {folder_id} not found"):
        await sut.execute(
            UpdateFolderParams(folder_id=folder_id, name="New", parent_folder_id=parent_folder_id)
        )
    repo.update.assert_not_awaited()
