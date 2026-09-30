import base64
import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.domain.entities.models.gallery_item import GalleryItem, GalleryItemSummary
from app.domain.entities.models.user import User
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.errors.domain_errors import (
    InvalidInputError,
    NotFoundError,
    PayloadTooLargeError,
)
from app.domain.usecases.gallery.create_gallery_item import CreateGalleryItem
from app.domain.usecases.gallery.delete_gallery_item import DeleteGalleryItem
from app.domain.usecases.gallery.get_gallery_item import GetGalleryItem
from app.domain.usecases.gallery.list_gallery_items import ListGalleryItems
from app.domain.usecases.gallery.rename_gallery_item import RenameGalleryItem
from app.main.main import app
from app.presentation.factories.gallery_factories import (
    create_gallery_item_factory,
    delete_gallery_item_factory,
    get_gallery_item_factory,
    list_gallery_items_factory,
    rename_gallery_item_factory,
)
from app.presentation.fastapi.dependencies.current_user import get_current_user

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
USER = User(email="ada@example.com", name="Ada")


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _override(factory: object, use_case: AsyncMock) -> None:
    app.dependency_overrides[factory] = lambda: use_case  # type: ignore[index]


def test_should_list_items_of_the_signed_in_user(client: TestClient) -> None:
    summary = GalleryItemSummary(
        owner_id=USER.id, name="Logo", kind=GalleryItemKind.IMAGE, thumbnail=PNG
    )
    use_case = AsyncMock(spec=ListGalleryItems)
    use_case.execute.return_value = [summary]
    _override(list_gallery_items_factory, use_case)
    app.dependency_overrides[get_current_user] = lambda: USER

    response = client.get("/gallery")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["name"] == "Logo"
    assert base64.b64decode(body[0]["thumbnail_base64"]) == PNG
    assert "image_base64" not in body[0]
    assert use_case.execute.await_args.args[0].owner_id == USER.id


def test_should_create_image_item_from_base64(client: TestClient) -> None:
    item = GalleryItem(
        name="Logo",
        kind=GalleryItemKind.IMAGE,
        image_data=PNG,
        image_mime_type=ImageMimeType.PNG,
    )
    use_case = AsyncMock(spec=CreateGalleryItem)
    use_case.execute.return_value = item
    _override(create_gallery_item_factory, use_case)

    response = client.post(
        "/gallery",
        json={
            "name": "Logo",
            "kind": "image",
            "image_base64": base64.b64encode(PNG).decode(),
            "thumbnail_base64": base64.b64encode(PNG).decode(),
        },
    )

    assert response.status_code == 201
    assert response.json()["image_mime_type"] == "image/png"
    params = use_case.execute.await_args.args[0]
    assert params.image_data == PNG
    assert params.thumbnail == PNG
    assert params.owner_id is None


def test_should_create_shapes_item(client: TestClient) -> None:
    content = {"shapes": [{"id": "shape:a"}], "rootShapeIds": ["shape:a"]}
    item = GalleryItem(name="Group", kind=GalleryItemKind.SHAPES, content=content)
    use_case = AsyncMock(spec=CreateGalleryItem)
    use_case.execute.return_value = item
    _override(create_gallery_item_factory, use_case)

    response = client.post("/gallery", json={"name": "Group", "kind": "shapes", "content": content})

    assert response.status_code == 201
    assert response.json()["content"] == content


def test_should_reject_unknown_kind(client: TestClient) -> None:
    response = client.post("/gallery", json={"name": "x", "kind": "video"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(InvalidInputError("bad"), 422), (PayloadTooLargeError("big"), 413)],
)
def test_should_map_validation_failures(
    client: TestClient, error: Exception, status_code: int
) -> None:
    use_case = AsyncMock(spec=CreateGalleryItem)
    use_case.execute.side_effect = error
    _override(create_gallery_item_factory, use_case)

    response = client.post("/gallery", json={"name": "x", "kind": "image", "image_base64": "AA=="})

    assert response.status_code == status_code


def test_should_get_item_with_payload(client: TestClient) -> None:
    item = GalleryItem(name="Logo", kind=GalleryItemKind.IMAGE, image_data=PNG)
    use_case = AsyncMock(spec=GetGalleryItem)
    use_case.execute.return_value = item
    _override(get_gallery_item_factory, use_case)

    response = client.get(f"/gallery/{item.id}")

    assert response.status_code == 200
    assert base64.b64decode(response.json()["image_base64"]) == PNG


def test_should_return_404_for_items_of_other_users(client: TestClient) -> None:
    use_case = AsyncMock(spec=GetGalleryItem)
    use_case.execute.side_effect = NotFoundError("Gallery item not found")
    _override(get_gallery_item_factory, use_case)

    response = client.get(f"/gallery/{uuid.uuid4()}")

    assert response.status_code == 404


def test_should_rename_item(client: TestClient) -> None:
    summary = GalleryItemSummary(name="Renamed", kind=GalleryItemKind.SHAPES)
    use_case = AsyncMock(spec=RenameGalleryItem)
    use_case.execute.return_value = summary
    _override(rename_gallery_item_factory, use_case)

    response = client.patch(f"/gallery/{summary.id}", json={"name": "Renamed"})

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_should_delete_item(client: TestClient) -> None:
    use_case = AsyncMock(spec=DeleteGalleryItem)
    use_case.execute.return_value = None
    _override(delete_gallery_item_factory, use_case)
    item_id = uuid.uuid4()

    response = client.delete(f"/gallery/{item_id}")

    assert response.status_code == 204
    assert use_case.execute.await_args.args[0].item_id == item_id
