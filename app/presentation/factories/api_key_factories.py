from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.api_key.create_api_key import CreateApiKey
from app.domain.usecases.api_key.list_api_keys import ListApiKeys
from app.domain.usecases.api_key.revoke_api_key import RevokeApiKey
from app.infra.database.repositories.api_key_repository import ApiKeyRepositoryImpl
from app.infra.database.session import get_session


async def create_api_key_factory(session: AsyncSession = Depends(get_session)) -> CreateApiKey:
    return CreateApiKey(ApiKeyRepositoryImpl(session))


async def list_api_keys_factory(session: AsyncSession = Depends(get_session)) -> ListApiKeys:
    return ListApiKeys(ApiKeyRepositoryImpl(session))


async def revoke_api_key_factory(session: AsyncSession = Depends(get_session)) -> RevokeApiKey:
    return RevokeApiKey(ApiKeyRepositoryImpl(session))
