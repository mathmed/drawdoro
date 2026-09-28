from app.domain.contracts.token_verifier import TokenVerifier
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.user_repository import UserRepository
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import UnauthorizedError


class AuthenticateUserParams(InputData):
    token: str


class AuthenticateUser(Usecase[AuthenticateUserParams, User]):
    def __init__(self, verifier: TokenVerifier, repo: UserRepository) -> None:
        self._verifier = verifier
        self._repo = repo

    async def execute(self, params: AuthenticateUserParams) -> User:
        if params.token == "":
            raise UnauthorizedError("Missing access token")
        identity = await self._verifier.verify(params.token)
        user = await self._repo.get_by_email(identity.email)
        if user is None:
            return await self._repo.create(User(email=identity.email, name=identity.name))
        if user.name != identity.name:
            user.name = identity.name
            return await self._repo.update(user)
        return user
