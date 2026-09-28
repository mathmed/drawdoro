import time
from dataclasses import dataclass
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.domain.errors.domain_errors import UnauthorizedError
from app.infra.auth.cognito_token_verifier import CognitoTokenVerifier

ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test"
CLIENT_ID = "client-123"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


@dataclass
class SigningKey:
    key: Any


class StaticKeys:
    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        return SigningKey(PRIVATE_KEY.public_key())


def make_token(**overrides: Any) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "sub": "sub-1",
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "token_use": "id",
        "email": "Ana@Example.com",
        "name": "Ana Souza",
        "iat": now,
        "exp": now + 300,
    }
    claims.update(overrides)
    return jwt.encode(
        {k: v for k, v in claims.items() if v is not None}, PRIVATE_KEY, algorithm="RS256"
    )


@pytest.fixture
def sut() -> CognitoTokenVerifier:
    return CognitoTokenVerifier(ISSUER, CLIENT_ID, StaticKeys())


async def test_should_return_identity_for_valid_id_token(sut: CognitoTokenVerifier) -> None:
    identity = await sut.verify(make_token())
    assert (identity.subject, identity.email, identity.name) == (
        "sub-1",
        "ana@example.com",
        "Ana Souza",
    )


async def test_should_build_name_from_given_and_family_names(sut: CognitoTokenVerifier) -> None:
    identity = await sut.verify(make_token(name=None, given_name="Ana", family_name="Souza"))
    assert identity.name == "Ana Souza"


async def test_should_fall_back_to_email_prefix_for_name(sut: CognitoTokenVerifier) -> None:
    identity = await sut.verify(make_token(name=None))
    assert identity.name == "Ana"


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "another-client"},
        {"iss": "https://evil.example.com"},
        {"exp": int(time.time()) - 10},
        {"token_use": "access"},
        {"email": None},
    ],
)
async def test_should_reject_invalid_tokens(
    sut: CognitoTokenVerifier, overrides: dict[str, Any]
) -> None:
    with pytest.raises(UnauthorizedError):
        await sut.verify(make_token(**overrides))


async def test_should_reject_token_signed_with_another_key(sut: CognitoTokenVerifier) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    forged = jwt.encode(
        {
            "sub": "x",
            "iss": ISSUER,
            "aud": CLIENT_ID,
            "token_use": "id",
            "email": "a@b.com",
            "iat": 1,
            "exp": 9999999999,
        },
        other_key,
        algorithm="RS256",
    )
    with pytest.raises(UnauthorizedError):
        await sut.verify(forged)
