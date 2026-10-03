from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.token_verifier import TokenVerifier
from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.identity import Identity
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import UnauthorizedError
from app.domain.usecases.auth.authenticate_user import AuthenticateUser, AuthenticateUserParams
from tests.doubles import double

IDENTITY = Identity(subject="sub-1", email="ana@example.com", name="Ana Souza")
PHOTO = "https://lh3.googleusercontent.com/a/photo"


@pytest.fixture
def verifier() -> NonCallableMagicMock:
    mock = double(TokenVerifier)
    mock.verify.return_value = IDENTITY
    return mock


@pytest.fixture
def repo() -> NonCallableMagicMock:
    mock = double(UserRepository)
    mock.create.side_effect = lambda user: user
    mock.update.side_effect = lambda user: user
    return mock


@pytest.fixture
def sut(verifier: NonCallableMagicMock, repo: NonCallableMagicMock) -> AuthenticateUser:
    return AuthenticateUser(verifier, repo)


async def test_should_create_user_on_first_sign_in(
    sut: AuthenticateUser, repo: NonCallableMagicMock, verifier: NonCallableMagicMock
) -> None:
    repo.get_by_email.return_value = None
    user = await sut.execute(AuthenticateUserParams(token="token"))
    assert (user.email, user.name) == ("ana@example.com", "Ana Souza")
    repo.create.assert_awaited_once()
    verifier.verify.assert_awaited_once_with("token")
    repo.get_by_email.assert_awaited_once_with("ana@example.com")


async def test_should_return_existing_user_unchanged(
    sut: AuthenticateUser, repo: NonCallableMagicMock
) -> None:
    existing = User(email="ana@example.com", name="Ana Souza")
    repo.get_by_email.return_value = existing
    assert await sut.execute(AuthenticateUserParams(token="token")) is existing
    repo.create.assert_not_awaited()
    repo.update.assert_not_awaited()


async def test_should_refresh_name_when_it_changed(
    sut: AuthenticateUser, repo: NonCallableMagicMock
) -> None:
    repo.get_by_email.return_value = User(email="ana@example.com", name="Ana")
    user = await sut.execute(AuthenticateUserParams(token="token"))
    assert user.name == "Ana Souza"
    repo.update.assert_awaited_once()


async def test_should_reject_missing_token(
    sut: AuthenticateUser, verifier: NonCallableMagicMock
) -> None:
    with pytest.raises(UnauthorizedError, match="^Missing access token$"):
        await sut.execute(AuthenticateUserParams(token=""))
    verifier.verify.assert_not_awaited()


async def test_should_propagate_invalid_token(
    sut: AuthenticateUser, verifier: NonCallableMagicMock
) -> None:
    verifier.verify.side_effect = UnauthorizedError("bad")
    with pytest.raises(UnauthorizedError):
        await sut.execute(AuthenticateUserParams(token="token"))


async def test_should_store_profile_photo_on_first_sign_in(
    sut: AuthenticateUser, verifier: NonCallableMagicMock, repo: NonCallableMagicMock
) -> None:
    verifier.verify.return_value = IDENTITY.model_copy(update={"picture_url": PHOTO})
    repo.get_by_email.return_value = None
    user = await sut.execute(AuthenticateUserParams(token="token"))
    assert user.picture_url == PHOTO


async def test_should_refresh_profile_photo_when_it_changed(
    sut: AuthenticateUser, verifier: NonCallableMagicMock, repo: NonCallableMagicMock
) -> None:
    verifier.verify.return_value = IDENTITY.model_copy(update={"picture_url": PHOTO})
    existing = User(email="ana@example.com", name="Ana Souza", picture_url=None)
    repo.get_by_email.return_value = existing
    user = await sut.execute(AuthenticateUserParams(token="token"))
    assert (user.name, user.picture_url) == ("Ana Souza", PHOTO)
    repo.update.assert_awaited_once()
