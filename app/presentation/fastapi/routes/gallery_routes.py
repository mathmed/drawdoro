import uuid

from fastapi import APIRouter, Depends

from app.domain.entities.models.user import User
from app.domain.usecases.gallery.create_gallery_item import (
    CreateGalleryItem,
    CreateGalleryItemParams,
)
from app.domain.usecases.gallery.delete_gallery_item import (
    DeleteGalleryItem,
    DeleteGalleryItemParams,
)
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem, GetGalleryItemParams
from app.domain.usecases.gallery.list_gallery_items import (
    ListGalleryItems,
    ListGalleryItemsParams,
)
from app.domain.usecases.gallery.rename_gallery_item import (
    RenameGalleryItem,
    RenameGalleryItemParams,
)
from app.presentation.factories.gallery_factories import (
    create_gallery_item_factory,
    delete_gallery_item_factory,
    get_gallery_item_factory,
    list_gallery_items_factory,
    rename_gallery_item_factory,
)
from app.presentation.fastapi.dependencies.current_user import get_current_user
from app.presentation.fastapi.schemas.gallery_schemas import (
    CreateGalleryItemRequest,
    GalleryItemResponse,
    GalleryItemSummaryResponse,
    RenameGalleryItemRequest,
)

# A personal gallery: every item belongs to the signed-in user and only they can see it.
router = APIRouter(prefix="/gallery", tags=["gallery"])


def _owner_id(user: User | None) -> uuid.UUID | None:
    return user.id if user is not None else None


@router.get("", response_model=list[GalleryItemSummaryResponse])
async def list_gallery_items(
    use_case: ListGalleryItems = Depends(list_gallery_items_factory),
    user: User | None = Depends(get_current_user),
) -> list[GalleryItemSummaryResponse]:
    items = await use_case.execute(ListGalleryItemsParams(owner_id=_owner_id(user)))
    return [GalleryItemSummaryResponse.model_validate(item) for item in items]


@router.post("", response_model=GalleryItemResponse, status_code=201)
async def create_gallery_item(
    body: CreateGalleryItemRequest,
    use_case: CreateGalleryItem = Depends(create_gallery_item_factory),
    user: User | None = Depends(get_current_user),
) -> GalleryItemResponse:
    item = await use_case.execute(
        CreateGalleryItemParams(
            owner_id=_owner_id(user),
            name=body.name,
            kind=body.kind,
            content=body.content,
            image_data=body.image_base64,
            thumbnail=body.thumbnail_base64,
        )
    )
    return GalleryItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=GalleryItemResponse)
async def get_gallery_item(
    item_id: uuid.UUID,
    use_case: GetGalleryItem = Depends(get_gallery_item_factory),
    user: User | None = Depends(get_current_user),
) -> GalleryItemResponse:
    item = await use_case.execute(GetGalleryItemParams(item_id=item_id, owner_id=_owner_id(user)))
    return GalleryItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=GalleryItemSummaryResponse)
async def rename_gallery_item(
    item_id: uuid.UUID,
    body: RenameGalleryItemRequest,
    use_case: RenameGalleryItem = Depends(rename_gallery_item_factory),
    user: User | None = Depends(get_current_user),
) -> GalleryItemSummaryResponse:
    item = await use_case.execute(
        RenameGalleryItemParams(item_id=item_id, owner_id=_owner_id(user), name=body.name)
    )
    return GalleryItemSummaryResponse.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def delete_gallery_item(
    item_id: uuid.UUID,
    use_case: DeleteGalleryItem = Depends(delete_gallery_item_factory),
    user: User | None = Depends(get_current_user),
) -> None:
    await use_case.execute(DeleteGalleryItemParams(item_id=item_id, owner_id=_owner_id(user)))
