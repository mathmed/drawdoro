from app.domain.constants.api_keys import API_KEY_PREFIX
from app.domain.services.api_key_secret import generate_api_key_secret, hash_api_key_secret


def test_should_generate_distinct_prefixed_secrets() -> None:
    first, second = generate_api_key_secret(), generate_api_key_secret()
    assert first.startswith(API_KEY_PREFIX)
    assert first != second
    assert len(first) > 40


def test_should_hash_deterministically_without_keeping_the_secret() -> None:
    secret = generate_api_key_secret()
    assert hash_api_key_secret(secret) == hash_api_key_secret(secret)
    assert secret not in hash_api_key_secret(secret)
    assert len(hash_api_key_secret(secret)) == 64
