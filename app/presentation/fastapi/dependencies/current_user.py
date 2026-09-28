import secrets

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.settings import Settings, get_settings
from app.domain.entities.models.user import User
from app.domain.usecases.auth.authenticate_user import AuthenticateUser, AuthenticateUserParams
from app.presentation.factories.auth_factories import authenticate_user_factory

bearer = HTTPBearer(auto_error=False)


def is_service_request(api_key: str | None, settings: Settings) -> bool:
    return (
        settings.service_api_key != ""
        and api_key is not None
        and secrets.compare_digest(api_key, settings.service_api_key)
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    use_case: AuthenticateUser = Depends(authenticate_user_factory),
) -> User | None:
    # None means "no user attached": auth is disabled or a trusted service is calling.
    if not settings.auth_enabled or is_service_request(x_api_key, settings):
        return None
    token = credentials.credentials if credentials is not None else ""
    return await use_case.execute(AuthenticateUserParams(token=token))
