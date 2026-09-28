from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.token_verifier import TokenVerifier
from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.identity import Identity
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser, AuthenticateUserParams

IDENTITY = Identity(subject="sub-1", email="ana@example.com", name="Ana Souza")


@pytest.fixture
def verifier() -> TokenVerifier:
    mock = cast(TokenVerifier, create_autospec(TokenVerifier))
    mock.verify = AsyncMock(return_value=IDENTITY)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def repo() -> UserRepository:
    mock = cast(UserRepository, create_autospec(UserRepository))
    mock.create = AsyncMock(side_effect=lambda user: user)  # type: ignore[method-assign]
    mock.update = AsyncMock(side_effect=lambda user: user)  # type: ignore[method-assign]
    return mock


@pytest.fixture
def sut(verifier: TokenVerifier, repo: UserRepository) -> AuthenticateUser:
    return AuthenticateUser(verifier, repo)


async def test_should_create_user_on_first_sign_in(
    sut: AuthenticateUser, repo: UserRepository
) -> None:
    repo.get_by_email = AsyncMock(return_value=None)  # type: ignore[method-assign]
    user = await sut.execute(AuthenticateUserParams(token="token"))
    assert (user.email, user.name) == ("ana@example.com", "Ana Souza")
    repo.create.assert_awaited_once()  # type: ignore[attr-defined]


async def test_should_return_existing_user_unchanged(
    sut: AuthenticateUser, repo: UserRepository
) -> None:
    existing = User(email="ana@example.com", name="Ana Souza")
    repo.get_by_email = AsyncMock(return_value=existing)  # type: ignore[method-assign]
    assert await sut.execute(AuthenticateUserParams(token="token")) is existing
    repo.create.assert_not_awaited()  # type: ignore[attr-defined]
    repo.update.assert_not_awaited()  # type: ignore[attr-defined]


async def test_should_refresh_name_when_it_changed(
    sut: AuthenticateUser, repo: UserRepository
) -> None:
    repo.get_by_email = AsyncMock(return_value=User(email="ana@example.com", name="Ana"))  # type: ignore[method-assign]
    user = await sut.execute(AuthenticateUserParams(token="token"))
    assert user.name == "Ana Souza"
    repo.update.assert_awaited_once()  # type: ignore[attr-defined]


async def test_should_reject_missing_token(sut: AuthenticateUser, verifier: TokenVerifier) -> None:
    with pytest.raises(UnauthorizedError):
        await sut.execute(AuthenticateUserParams(token=""))
    verifier.verify.assert_not_awaited()  # type: ignore[attr-defined]


async def test_should_propagate_invalid_token(
    sut: AuthenticateUser, verifier: TokenVerifier
) -> None:
    verifier.verify = AsyncMock(side_effect=UnauthorizedError("bad"))  # type: ignore[method-assign]
    with pytest.raises(UnauthorizedError):
        await sut.execute(AuthenticateUserParams(token="token"))
