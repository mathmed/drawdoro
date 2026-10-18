import uuid
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.entities.models.folder import Folder
from app.domain.entities.models.project import Project
from app.domain.errors.domain_errors import NotFoundError
from app.domain.services.project_placement import ProjectPlacement
from tests.doubles import double

PROJECT_ID = uuid.uuid4()


@pytest.fixture
def projects() -> NonCallableMagicMock:
    repo = double(ProjectRepository)
    repo.get_by_id.return_value = Project(id=PROJECT_ID, workspace_id=uuid.uuid4(), name="Shop")
    return repo


@pytest.fixture
def folders() -> NonCallableMagicMock:
    return double(FolderRepository)


@pytest.fixture
def sut(projects: NonCallableMagicMock, folders: NonCallableMagicMock) -> ProjectPlacement:
    return ProjectPlacement(projects, folders)


def folder_in(project_id: uuid.UUID) -> Folder:
    return Folder(project_id=project_id, name="Docs")


async def test_should_accept_a_new_item_at_the_root_of_an_existing_project(
    sut: ProjectPlacement, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    await sut.check_new(PROJECT_ID, None)
    projects.get_by_id.assert_awaited_once_with(PROJECT_ID)
    folders.get_by_id.assert_not_awaited()


async def test_should_accept_a_new_item_in_a_folder_of_the_project(
    sut: ProjectPlacement, folders: NonCallableMagicMock
) -> None:
    folder = folder_in(PROJECT_ID)
    folders.get_by_id.return_value = folder
    await sut.check_new(PROJECT_ID, folder.id)
    folders.get_by_id.assert_awaited_once_with(folder.id)


async def test_should_report_a_missing_project_as_not_found(
    sut: ProjectPlacement, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    projects.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"^Project {PROJECT_ID} not found$"):
        await sut.check_new(PROJECT_ID, uuid.uuid4())
    folders.get_by_id.assert_not_awaited()


async def test_should_report_a_missing_folder_of_a_new_item_as_not_found(
    sut: ProjectPlacement, folders: NonCallableMagicMock
) -> None:
    folder_id = uuid.uuid4()
    folders.get_by_id.return_value = None
    with pytest.raises(NotFoundError, match=f"^Folder {folder_id} not found$"):
        await sut.check_new(PROJECT_ID, folder_id)


async def test_should_report_a_folder_of_another_project_as_not_found(
    sut: ProjectPlacement, folders: NonCallableMagicMock
) -> None:
    folder = folder_in(uuid.uuid4())
    folders.get_by_id.return_value = folder
    with pytest.raises(NotFoundError, match=f"^Folder {folder.id} not found$"):
        await sut.check_new(PROJECT_ID, folder.id)


async def test_should_accept_a_move_to_a_folder_of_the_project(
    sut: ProjectPlacement, projects: NonCallableMagicMock, folders: NonCallableMagicMock
) -> None:
    folder = folder_in(PROJECT_ID)
    folders.get_by_id.return_value = folder
    await sut.check_move(PROJECT_ID, uuid.uuid4(), folder.id)
    folders.get_by_id.assert_awaited_once_with(folder.id)
    projects.get_by_id.assert_not_awaited()


async def test_should_accept_a_move_to_the_root(
    sut: ProjectPlacement, folders: NonCallableMagicMock
) -> None:
    await sut.check_move(PROJECT_ID, uuid.uuid4(), None)
    folders.get_by_id.assert_not_awaited()


async def test_should_not_check_the_folder_an_item_stays_in(
    sut: ProjectPlacement, folders: NonCallableMagicMock
) -> None:
    deleted_folder_id = uuid.uuid4()
    folders.get_by_id.return_value = None
    await sut.check_move(PROJECT_ID, deleted_folder_id, deleted_folder_id)
    folders.get_by_id.assert_not_awaited()


@pytest.mark.parametrize("owner", [None, uuid.uuid4()], ids=["missing", "another-project"])
async def test_should_report_a_move_to_a_folder_out_of_reach_as_not_found(
    sut: ProjectPlacement, folders: NonCallableMagicMock, owner: uuid.UUID | None
) -> None:
    folder_id = uuid.uuid4()
    folders.get_by_id.return_value = None if owner is None else folder_in(owner)
    with pytest.raises(NotFoundError, match=f"^Folder {folder_id} not found$"):
        await sut.check_move(PROJECT_ID, None, folder_id)
