import uuid
from datetime import UTC, datetime
from unittest.mock import NonCallableMagicMock

import pytest

from app.domain.contracts.diagram_thumbnail_repository import DiagramThumbnailRepository
from app.domain.entities.models.diagram_thumbnail import DiagramThumbnail
from app.domain.enums.image_mime_type import ImageMimeType
from app.domain.enums.thumbnail_theme import ThumbnailTheme
from app.domain.usecases.diagram.list_diagram_thumbnails import (
    ListDiagramThumbnails,
    ListDiagramThumbnailsParams,
)
from tests.doubles import double


@pytest.fixture
def repo() -> NonCallableMagicMock:
    return double(DiagramThumbnailRepository)


@pytest.fixture
def sut(repo: NonCallableMagicMock) -> ListDiagramThumbnails:
    return ListDiagramThumbnails(repo)


async def test_should_list_the_project_thumbnails_in_the_requested_theme(
    sut: ListDiagramThumbnails, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    thumbnail = DiagramThumbnail(
        diagram_id=uuid.uuid4(),
        theme=ThumbnailTheme.DARK,
        version=datetime.now(UTC),
        image=b"\x89PNG\r\n\x1a\n",
        mime_type=ImageMimeType.PNG,
    )
    repo.list_by_project.return_value = [thumbnail]

    result = await sut.execute(
        ListDiagramThumbnailsParams(project_id=project_id, theme=ThumbnailTheme.DARK)
    )

    assert result == [thumbnail]
    repo.list_by_project.assert_awaited_once_with(project_id, ThumbnailTheme.DARK)


async def test_should_list_light_thumbnails_by_default(
    sut: ListDiagramThumbnails, repo: NonCallableMagicMock
) -> None:
    project_id = uuid.uuid4()
    repo.list_by_project.return_value = []

    assert await sut.execute(ListDiagramThumbnailsParams(project_id=project_id)) == []
    repo.list_by_project.assert_awaited_once_with(project_id, ThumbnailTheme.LIGHT)
