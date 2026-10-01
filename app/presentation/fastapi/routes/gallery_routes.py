import uuid

from fastapi import APIRouter, Depends, Query

from app.domain.constants.gallery import GALLERY_MAX_LISTED_ITEMS
from app.domain.entities.models.revision_author import RevisionAuthor
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.usecases.gallery.create_gallery_item import (
    CreateGalleryItem,
    CreateGalleryItemParams,
)
from app.domain.usecases.gallery.delete_gallery_item import (
    DeleteGalleryItem,
    DeleteGalleryItemParams,
)
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem, GetGalleryItemParams
from app.domain.usecases.gallery.insert_gallery_item import (
    InsertGalleryItem,
    InsertGalleryItemParams,
)
from app.domain.usecases.gallery.list_gallery_items import (
    ListGalleryItems,
    ListGalleryItemsParams,
)
from app.domain.usecases.gallery.update_gallery_item import (
    UpdateGalleryItem,
    UpdateGalleryItemParams,
)
from app.presentation.factories.gallery_factories import (
    create_gallery_item_factory,
    delete_gallery_item_factory,
    get_gallery_item_factory,
    insert_gallery_item_factory,
    list_gallery_items_factory,
    update_gallery_item_factory,
)
from app.presentation.fastapi.dependencies.agent_presence import track_agent_activity
from app.presentation.fastapi.dependencies.gallery_owner import get_gallery_owner_id
from app.presentation.fastapi.dependencies.revision_author import get_revision_author
from app.presentation.fastapi.dependencies.workspace_access import require_workspace_access
from app.presentation.fastapi.schemas.gallery_schemas import (
    CreateGalleryItemRequest,
    GalleryInsertionResponse,
    GalleryItemResponse,
    GalleryItemSummaryResponse,
    InsertGalleryItemRequest,
    UpdateGalleryItemRequest,
)

# A personal gallery: every item belongs to the signed-in user (or the owner of the personal key)
# and only they can see it.
router = APIRouter(prefix="/gallery", tags=["gallery"])

# Inserting writes to a diagram, so it also needs the editor role in the diagram's workspace.
insertion_router = APIRouter(
    prefix="/diagrams/{diagram_id}/gallery-insertions",
    tags=["gallery"],
    dependencies=[Depends(require_workspace_access), Depends(track_agent_activity)],
)


@router.get("", response_model=list[GalleryItemSummaryResponse])
async def list_gallery_items(
    query: str | None = Query(default=None, max_length=200),
    kind: GalleryItemKind | None = Query(default=None),
    tag: str | None = Query(default=None, max_length=100),
    limit: int | None = Query(default=None, ge=1, le=GALLERY_MAX_LISTED_ITEMS),
    include_thumbnails: bool = Query(default=True),
    use_case: ListGalleryItems = Depends(list_gallery_items_factory),
    owner_id: uuid.UUID | None = Depends(get_gallery_owner_id),
) -> list[GalleryItemSummaryResponse]:
    items = await use_case.execute(
        ListGalleryItemsParams(
            owner_id=owner_id,
            query=query,
            kind=kind,
            tag=tag,
            limit=limit,
            include_thumbnails=include_thumbnails,
        )
    )
    return [GalleryItemSummaryResponse.model_validate(item) for item in items]


@router.post("", response_model=GalleryItemResponse, status_code=201)
async def create_gallery_item(
    body: CreateGalleryItemRequest,
    use_case: CreateGalleryItem = Depends(create_gallery_item_factory),
    owner_id: uuid.UUID | None = Depends(get_gallery_owner_id),
) -> GalleryItemResponse:
    item = await use_case.execute(
        CreateGalleryItemParams(
            owner_id=owner_id,
            name=body.name,
            kind=body.kind,
            content=body.content,
            image_data=body.image_base64,
            thumbnail=body.thumbnail_base64,
            tags=body.tags,
            description=body.description,
        )
    )
    return GalleryItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=GalleryItemResponse)
async def get_gallery_item(
    item_id: uuid.UUID,
    use_case: GetGalleryItem = Depends(get_gallery_item_factory),
    owner_id: uuid.UUID | None = Depends(get_gallery_owner_id),
) -> GalleryItemResponse:
    item = await use_case.execute(GetGalleryItemParams(item_id=item_id, owner_id=owner_id))
    return GalleryItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=GalleryItemSummaryResponse)
async def update_gallery_item(
    item_id: uuid.UUID,
    body: UpdateGalleryItemRequest,
    use_case: UpdateGalleryItem = Depends(update_gallery_item_factory),
    owner_id: uuid.UUID | None = Depends(get_gallery_owner_id),
) -> GalleryItemSummaryResponse:
    item = await use_case.execute(
        UpdateGalleryItemParams(
            item_id=item_id,
            owner_id=owner_id,
            name=body.name,
            tags=body.tags,
            description=body.description,
        )
    )
    return GalleryItemSummaryResponse.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def delete_gallery_item(
    item_id: uuid.UUID,
    use_case: DeleteGalleryItem = Depends(delete_gallery_item_factory),
    owner_id: uuid.UUID | None = Depends(get_gallery_owner_id),
) -> None:
    await use_case.execute(DeleteGalleryItemParams(item_id=item_id, owner_id=owner_id))


@insertion_router.post("", response_model=GalleryInsertionResponse, status_code=201)
async def insert_gallery_item(
    diagram_id: uuid.UUID,
    body: InsertGalleryItemRequest,
    owner_id: uuid.UUID | None = Depends(get_gallery_owner_id),
    author: RevisionAuthor = Depends(get_revision_author),
    use_case: InsertGalleryItem = Depends(insert_gallery_item_factory),
) -> GalleryInsertionResponse:
    inserted = await use_case.execute(
        InsertGalleryItemParams(
            diagram_id=diagram_id,
            item_id=body.item_id,
            owner_id=owner_id,
            x=body.x,
            y=body.y,
            near_shape_id=body.near_shape_id,
            side=body.side,
            gap=body.gap,
            scale=body.scale,
            author=author,
            revision_summary=body.revision_summary,
        )
    )
    return GalleryInsertionResponse(
        diagram_id=inserted.diagram.id,
        item_id=inserted.item_id,
        updated_at=inserted.diagram.updated_at,
        created_ids=inserted.created_ids,
        root_shape_ids=inserted.root_shape_ids,
        x=inserted.x,
        y=inserted.y,
        width=inserted.width,
        height=inserted.height,
    )
