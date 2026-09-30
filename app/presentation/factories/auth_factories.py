from functools import lru_cache

import jwt
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.settings import get_settings
from app.domain.usecases.auth.authenticate_api_key import AuthenticateApiKey
from app.domain.usecases.auth.authenticate_user import AuthenticateUser
from app.domain.usecases.auth.authorize_workspace_access import AuthorizeWorkspaceAccess
from app.infra.auth.cognito_token_verifier import CognitoTokenVerifier
from app.infra.database.repositories.api_key_repository import ApiKeyRepositoryImpl
from app.infra.database.repositories.diagram_repository import DiagramRepositoryImpl
from app.infra.database.repositories.folder_repository import FolderRepositoryImpl
from app.infra.database.repositories.project_repository import ProjectRepositoryImpl
from app.infra.database.repositories.user_repository import UserRepositoryImpl
from app.infra.database.repositories.workspace_member_repository import (
    WorkspaceMemberRepositoryImpl,
)
from app.infra.database.session import get_session


@lru_cache
def get_token_verifier() -> CognitoTokenVerifier:
    settings = get_settings()
    # One JWKS client per process so the user pool's signing keys are fetched once and cached.
    keys = jwt.PyJWKClient(f"{settings.cognito_issuer}/.well-known/jwks.json", cache_keys=True)
    return CognitoTokenVerifier(settings.cognito_issuer, settings.cognito_client_id, keys)


async def authenticate_user_factory(
    session: AsyncSession = Depends(get_session),
) -> AuthenticateUser:
    return AuthenticateUser(get_token_verifier(), UserRepositoryImpl(session))


async def authenticate_api_key_factory(
    session: AsyncSession = Depends(get_session),
) -> AuthenticateApiKey:
    return AuthenticateApiKey(ApiKeyRepositoryImpl(session), UserRepositoryImpl(session))


async def authorize_workspace_access_factory(
    session: AsyncSession = Depends(get_session),
) -> AuthorizeWorkspaceAccess:
    return AuthorizeWorkspaceAccess(
        WorkspaceMemberRepositoryImpl(session),
        ProjectRepositoryImpl(session),
        FolderRepositoryImpl(session),
        DiagramRepositoryImpl(session),
    )
