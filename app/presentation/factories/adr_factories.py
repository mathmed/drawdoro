from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.adr.create_adr import CreateAdr
from app.domain.usecases.adr.delete_adr import DeleteAdr
from app.domain.usecases.adr.get_adr import GetAdr
from app.domain.usecases.adr.list_adrs import ListAdrs
from app.domain.usecases.adr.update_adr import UpdateAdr
from app.infra.database.repositories.adr_repository import AdrRepositoryImpl
from app.infra.database.session import get_session


async def create_adr_factory(session: AsyncSession = Depends(get_session)) -> CreateAdr:
    return CreateAdr(AdrRepositoryImpl(session))


async def get_adr_factory(session: AsyncSession = Depends(get_session)) -> GetAdr:
    return GetAdr(AdrRepositoryImpl(session))


async def list_adrs_factory(session: AsyncSession = Depends(get_session)) -> ListAdrs:
    return ListAdrs(AdrRepositoryImpl(session))


async def update_adr_factory(session: AsyncSession = Depends(get_session)) -> UpdateAdr:
    return UpdateAdr(AdrRepositoryImpl(session))


async def delete_adr_factory(session: AsyncSession = Depends(get_session)) -> DeleteAdr:
    return DeleteAdr(AdrRepositoryImpl(session))
