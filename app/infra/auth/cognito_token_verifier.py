import asyncio
from typing import Any, Protocol

import jwt

from app.domain.contracts.token_verifier import TokenVerifier
from app.domain.entities.models.identity import Identity
from app.domain.errors.domain_errors import UnauthorizedError


class SigningKeyProvider(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


class CognitoTokenVerifier(TokenVerifier):
    # Verifies Cognito ID tokens: they carry the email and name we store, while the
    # audience check ties them to our app client.
    def __init__(self, issuer: str, client_id: str, keys: SigningKeyProvider) -> None:
        self._issuer = issuer
        self._client_id = client_id
        self._keys = keys

    async def verify(self, token: str) -> Identity:
        try:
            # Fetching the JWKS is blocking I/O (cached after the first call).
            signing_key = await asyncio.to_thread(self._keys.get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except jwt.PyJWTError as error:
            raise UnauthorizedError("Invalid or expired token") from error

        if claims.get("token_use") != "id":
            raise UnauthorizedError("An ID token is required")
        email = claims.get("email")
        if not isinstance(email, str) or email == "":
            raise UnauthorizedError("Token has no email")
        return Identity(
            subject=claims["sub"], email=email.lower(), name=_display_name(claims, email)
        )


def _display_name(claims: dict[str, Any], email: str) -> str:
    name = claims.get("name")
    if isinstance(name, str) and name.strip() != "":
        return name.strip()
    parts = [claims.get("given_name"), claims.get("family_name")]
    full = " ".join(part for part in parts if isinstance(part, str) and part != "")
    return full or email.split("@")[0]
