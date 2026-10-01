import uuid

from fastapi import Depends

from app.domain.errors.domain_errors import ForbiddenError
from app.presentation.fastapi.dependencies.current_user import Caller, get_caller

PERSONAL_GALLERY_ONLY = (
    "The gallery is personal: it belongs to one person and only works with a signed-in session "
    "or that person's personal API key. The shared service key has no owner, so it has no "
    "gallery. Create a personal key under Connect Claude and use it instead."
)


# Whose gallery a request works on. None only when authentication is disabled (local
# development), where the items without owner are the shared gallery.
async def get_gallery_owner_id(caller: Caller = Depends(get_caller)) -> uuid.UUID | None:
    if caller.is_service:
        raise ForbiddenError(PERSONAL_GALLERY_ONLY)
    return caller.user.id if caller.user is not None else None
