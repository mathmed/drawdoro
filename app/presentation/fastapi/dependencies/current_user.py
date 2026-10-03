import secrets
from dataclasses import dataclass

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.settings import Settings, get_settings
from app.domain.constants.api_keys import API_KEY_PREFIX
from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError
from app.domain.usecases.auth.authenticate_api_key import (
    AuthenticateApiKey,
    AuthenticateApiKeyParams,
)
from app.domain.usecases.auth.authenticate_user import AuthenticateUser, AuthenticateUserParams
from app.presentation.factories.auth_factories import (
    authenticate_api_key_factory,
    authenticate_user_factory,
)

bearer = HTTPBearer(auto_error=False)


# Who is calling: a signed-in person, an agent with its owner's personal key, the shared service
# key (an agent without owner), or nobody when authentication is disabled.
@dataclass(frozen=True)
class Caller:
    user: User | None = None
    api_key: ApiKey | None = None
    is_service: bool = False


def is_service_request(api_key: str | None, settings: Settings) -> bool:
    return (
        settings.service_api_key != ""
        and api_key is not None
        and secrets.compare_digest(api_key, settings.service_api_key)
    )


async def get_caller(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    authenticate: AuthenticateUser = Depends(authenticate_user_factory),
    authenticate_key: AuthenticateApiKey = Depends(authenticate_api_key_factory),
) -> Caller:
    if not settings.auth_enabled:
        return Caller()
    if is_service_request(x_api_key, settings):
        return Caller(is_service=True)
    # Other values keep the old behaviour of falling back to the session token.
    if x_api_key is not None and x_api_key.startswith(API_KEY_PREFIX):
        owner = await authenticate_key.execute(AuthenticateApiKeyParams(secret=x_api_key))
        return Caller(user=owner.user, api_key=owner.api_key)
    token = _bearer_token(credentials)
    return Caller(user=await authenticate.execute(AuthenticateUserParams(token=token)))


def _bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    return credentials.credentials if credentials is not None else ""


async def get_current_user(caller: Caller = Depends(get_caller)) -> User | None:
    # None means "no user attached": auth is disabled or a trusted service is calling.
    return caller.user


# Personal keys are managed from a browser session only, so a leaked key can't mint more keys.
async def get_session_user(caller: Caller = Depends(get_caller)) -> User:
    if caller.api_key is not None:
        raise ForbiddenError("API keys can only be managed from a signed-in session")
    if caller.user is None:
        raise NotFoundError("No signed-in user (authentication is disabled)")
    return caller.user
