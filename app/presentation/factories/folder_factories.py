from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.folder.create_folder import CreateFolder
from app.domain.usecases.folder.delete_folder import DeleteFolder
from app.domain.usecases.folder.get_folder import GetFolder
from app.domain.usecases.folder.list_folders import ListFolders
from app.domain.usecases.folder.update_folder import UpdateFolder
from app.infra.database.repositories.folder_repository import FolderRepositoryImpl
from app.infra.database.session import get_session


async def create_folder_factory(session: AsyncSession = Depends(get_session)) -> CreateFolder:
    return CreateFolder(FolderRepositoryImpl(session))


async def get_folder_factory(session: AsyncSession = Depends(get_session)) -> GetFolder:
    return GetFolder(FolderRepositoryImpl(session))


async def list_folders_factory(session: AsyncSession = Depends(get_session)) -> ListFolders:
    return ListFolders(FolderRepositoryImpl(session))


async def update_folder_factory(session: AsyncSession = Depends(get_session)) -> UpdateFolder:
    return UpdateFolder(FolderRepositoryImpl(session))


async def delete_folder_factory(session: AsyncSession = Depends(get_session)) -> DeleteFolder:
    return DeleteFolder(FolderRepositoryImpl(session))
