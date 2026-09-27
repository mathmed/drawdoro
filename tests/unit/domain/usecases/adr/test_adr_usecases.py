import uuid
from typing import cast
from unittest.mock import AsyncMock, create_autospec

import pytest

from app.domain.contracts.adr_repository import AdrRepository
from app.domain.entities.models.adr import Adr
from app.domain.enums.adr_status import AdrStatus
from app.domain.errors.domain_errors import NotFoundError
from app.domain.usecases.adr.create_adr import CreateAdr, CreateAdrParams
from app.domain.usecases.adr.delete_adr import DeleteAdr, DeleteAdrParams
from app.domain.usecases.adr.get_adr import GetAdr, GetAdrParams
from app.domain.usecases.adr.update_adr import UpdateAdr, UpdateAdrParams


@pytest.fixture
def repo() -> AdrRepository:
    return cast(AdrRepository, create_autospec(AdrRepository))


def _make_adr(diagram_id: uuid.UUID) -> Adr:
    return Adr(
        diagram_id=diagram_id,
        title="Use PostgreSQL",
        context="need db",
        decision="use pg",
        consequences="manage db",
        status=AdrStatus.PROPOSED,
    )


async def test_should_create_adr(repo: AdrRepository) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    repo.create = AsyncMock(return_value=adr)  # type: ignore[method-assign]
    sut = CreateAdr(repo)
    params = CreateAdrParams(
        diagram_id=diagram_id,
        title="Use PostgreSQL",
        context="need db",
        decision="use pg",
        consequences="manage db",
    )
    result = await sut.execute(params)
    assert result.title == "Use PostgreSQL"
    repo.create.assert_awaited_once()


async def test_should_get_adr(repo: AdrRepository) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    repo.get_by_id = AsyncMock(return_value=adr)  # type: ignore[method-assign]
    sut = GetAdr(repo)
    result = await sut.execute(GetAdrParams(adr_id=adr.id))
    assert result.id == adr.id


async def test_should_raise_not_found_when_adr_missing(repo: AdrRepository) -> None:
    repo.get_by_id = AsyncMock(return_value=None)  # type: ignore[method-assign]
    sut = GetAdr(repo)
    with pytest.raises(NotFoundError):
        await sut.execute(GetAdrParams(adr_id=uuid.uuid4()))


async def test_should_update_adr(repo: AdrRepository) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    repo.get_by_id = AsyncMock(return_value=adr)  # type: ignore[method-assign]
    repo.update = AsyncMock(return_value=adr)  # type: ignore[method-assign]
    sut = UpdateAdr(repo)
    params = UpdateAdrParams(
        adr_id=adr.id,
        title="Updated",
        context="ctx",
        decision="dec",
        consequences="cons",
        status=AdrStatus.ACCEPTED,
    )
    result = await sut.execute(params)
    assert result is not None


async def test_should_delete_adr(repo: AdrRepository) -> None:
    diagram_id = uuid.uuid4()
    adr = _make_adr(diagram_id)
    repo.get_by_id = AsyncMock(return_value=adr)  # type: ignore[method-assign]
    repo.delete = AsyncMock()  # type: ignore[method-assign]
    sut = DeleteAdr(repo)
    await sut.execute(DeleteAdrParams(adr_id=adr.id))
    repo.delete.assert_awaited_once_with(adr.id)
