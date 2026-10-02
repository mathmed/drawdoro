import pytest

from app.domain.entities.models.api_key import ApiKey
from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import ForbiddenError
from app.presentation.fastapi.dependencies.current_user import Caller
from app.presentation.fastapi.dependencies.gallery_owner import (
    PERSONAL_GALLERY_ONLY,
    get_gallery_owner_id,
)

ANA = User(email="ana@example.com", name="Ana")


async def test_should_use_the_signed_in_person() -> None:
    assert await get_gallery_owner_id(Caller(user=ANA)) == ANA.id


async def test_should_use_the_owner_of_a_personal_key() -> None:
    key = ApiKey(user_id=ANA.id, label="laptop", prefix="mcpk_x", key_hash="h")
    assert await get_gallery_owner_id(Caller(user=ANA, api_key=key)) == ANA.id


async def test_should_use_the_shared_gallery_without_authentication() -> None:
    assert await get_gallery_owner_id(Caller()) is None


async def test_should_refuse_the_service_key() -> None:
    with pytest.raises(ForbiddenError) as raised:
        await get_gallery_owner_id(Caller(is_service=True))
    assert raised.value.message == PERSONAL_GALLERY_ONLY
    assert "personal API key" in PERSONAL_GALLERY_ONLY
