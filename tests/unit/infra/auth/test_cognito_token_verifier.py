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
    def __init__(self) -> None:
        self.requested: list[str] = []

    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        self.requested.append(token)
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
def keys() -> StaticKeys:
    return StaticKeys()


@pytest.fixture
def sut(keys: StaticKeys) -> CognitoTokenVerifier:
    return CognitoTokenVerifier(ISSUER, CLIENT_ID, keys)


# The signing key is looked up from the token's own header (its key id).
async def test_should_fetch_the_signing_key_of_the_token(
    sut: CognitoTokenVerifier, keys: StaticKeys
) -> None:
    token = make_token()
    await sut.verify(token)
    assert keys.requested == [token]


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
    ("claims", "expected"),
    [
        ({"name": "  Ana Souza  "}, "Ana Souza"),
        ({"name": "   ", "given_name": "Ana", "family_name": "Souza"}, "Ana Souza"),
        ({"name": None, "given_name": "Ana", "family_name": ""}, "Ana"),
        ({"name": None, "given_name": "", "family_name": "Souza"}, "Souza"),
        ({"name": None, "family_name": "Souza"}, "Souza"),
        ({"name": None, "given_name": 7, "family_name": "Souza"}, "Souza"),
        ({"name": 7, "given_name": "Ana"}, "Ana"),
        ({"name": "", "given_name": "", "family_name": ""}, "Ana"),
    ],
)
async def test_should_pick_the_display_name_from_the_best_claim(
    sut: CognitoTokenVerifier, claims: dict[str, Any], expected: str
) -> None:
    identity = await sut.verify(make_token(**claims))
    assert identity.name == expected


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"aud": "another-client"}, "Invalid or expired token"),
        ({"iss": "https://evil.example.com"}, "Invalid or expired token"),
        ({"exp": int(time.time()) - 10}, "Invalid or expired token"),
        ({"exp": None}, "Invalid or expired token"),
        ({"iat": None}, "Invalid or expired token"),
        ({"sub": None}, "Invalid or expired token"),
        ({"token_use": "access"}, "An ID token is required"),
        ({"token_use": None}, "An ID token is required"),
        ({"email": None}, "Token has no email"),
        ({"email": ""}, "Token has no email"),
        ({"email": 42}, "Token has no email"),
    ],
)
async def test_should_reject_invalid_tokens(
    sut: CognitoTokenVerifier, overrides: dict[str, Any], message: str
) -> None:
    with pytest.raises(UnauthorizedError) as rejected:
        await sut.verify(make_token(**overrides))
    assert rejected.value.message == message


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
    with pytest.raises(UnauthorizedError, match="Invalid or expired token"):
        await sut.verify(forged)


async def test_should_return_profile_photo_from_picture_claim(sut: CognitoTokenVerifier) -> None:
    photo = "https://lh3.googleusercontent.com/a/photo=s96-c"
    identity = await sut.verify(make_token(picture=photo))
    assert identity.picture_url == photo


async def test_should_keep_a_profile_photo_url_of_the_maximum_length(
    sut: CognitoTokenVerifier,
) -> None:
    photo = "https://x/" + "a" * (2048 - len("https://x/"))
    identity = await sut.verify(make_token(picture=photo))
    assert identity.picture_url == photo


@pytest.mark.parametrize(
    "picture",
    [
        None,
        "",
        7,
        "http://example.com/photo.png",
        "javascript:alert(1)",
        "https://x/" + "a" * 2048,
    ],
)
async def test_should_ignore_missing_or_unsafe_profile_photo(
    sut: CognitoTokenVerifier, picture: object
) -> None:
    identity = await sut.verify(make_token(picture=picture))
    assert identity.picture_url is None
