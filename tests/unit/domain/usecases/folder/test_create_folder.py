import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.usecases.folder.create_folder import CreateFolder, CreateFolderParams
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(FolderRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> CreateFolder:
    return CreateFolder(repo)


async def test_should_create_the_folder_from_the_params(
    sut: CreateFolder, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    parent_folder_id = uuid.uuid4()
    repo.create.side_effect = lambda folder: folder
    result = await sut.execute(
        CreateFolderParams(project_id=project_id, name="Docs", parent_folder_id=parent_folder_id)
    )
    created = repo.create.await_args.args[0]
    assert result is created
    assert created.project_id == project_id
    assert created.name == "Docs"
    assert created.parent_folder_id == parent_folder_id


async def test_should_create_a_root_folder_by_default(
    sut: CreateFolder, repo: NonCallableMagicMock
) -> None:
    repo.create.side_effect = lambda folder: folder
    result = await sut.execute(CreateFolderParams(project_id=uuid.uuid4(), name="Docs"))
    assert result.parent_folder_id is None
