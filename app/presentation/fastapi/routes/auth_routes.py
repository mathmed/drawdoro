from fastapi import APIRouter, Depends

from app.domain.entities.models.user import User
from app.domain.errors.domain_errors import NotFoundError
from app.presentation.fastapi.dependencies.current_user import get_current_user
from app.presentation.fastapi.schemas.user_schemas import UserResponse

router = APIRouter(prefix="/me", tags=["auth"])


@router.get("", response_model=UserResponse)
async def get_me(user: User | None = Depends(get_current_user)) -> UserResponse:
    if user is None:
        raise NotFoundError("No signed-in user (authentication is disabled)")
    return UserResponse.model_validate(user)
