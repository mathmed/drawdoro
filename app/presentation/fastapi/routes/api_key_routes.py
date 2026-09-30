import uuid

from fastapi import APIRouter, Depends

from app.domain.entities.models.user import User
from app.domain.usecases.api_key.create_api_key import CreateApiKey, CreateApiKeyParams
from app.domain.usecases.api_key.list_api_keys import ListApiKeys, ListApiKeysParams
from app.domain.usecases.api_key.revoke_api_key import RevokeApiKey, RevokeApiKeyParams
from app.presentation.factories.api_key_factories import (
    create_api_key_factory,
    list_api_keys_factory,
    revoke_api_key_factory,
)
from app.presentation.fastapi.dependencies.current_user import get_session_user
from app.presentation.fastapi.schemas.api_key_schemas import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreatedApiKeyResponse,
)

# Personal keys the signed-in user hands to their agents (the MCP server) to act on their behalf.
router = APIRouter(prefix="/me/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user: User = Depends(get_session_user),
    use_case: ListApiKeys = Depends(list_api_keys_factory),
) -> list[ApiKeyResponse]:
    keys = await use_case.execute(ListApiKeysParams(user_id=user.id))
    return [ApiKeyResponse.model_validate(key) for key in keys]


@router.post("", response_model=CreatedApiKeyResponse, status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    user: User = Depends(get_session_user),
    use_case: CreateApiKey = Depends(create_api_key_factory),
) -> CreatedApiKeyResponse:
    created = await use_case.execute(CreateApiKeyParams(user_id=user.id, label=body.label))
    return CreatedApiKeyResponse.model_validate(
        created.api_key.model_dump() | {"secret": created.secret}
    )


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    user: User = Depends(get_session_user),
    use_case: RevokeApiKey = Depends(revoke_api_key_factory),
) -> None:
    await use_case.execute(RevokeApiKeyParams(user_id=user.id, key_id=key_id))
