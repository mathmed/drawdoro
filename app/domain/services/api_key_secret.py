import hashlib
import secrets

from app.domain.constants.api_keys import API_KEY_PREFIX, API_KEY_SECRET_BYTES


def generate_api_key_secret(secret_bytes: int = API_KEY_SECRET_BYTES) -> str:
    return API_KEY_PREFIX + secrets.token_urlsafe(secret_bytes)


# The secrets are long and random, so a fast unsalted hash is enough to make a leaked table
# useless while keeping the lookup on every agent call a single indexed query.
def hash_api_key_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()
