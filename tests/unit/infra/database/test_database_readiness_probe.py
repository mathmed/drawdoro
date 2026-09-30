import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

import app.infra.database.database_readiness_probe as probe_module
from app.infra.database.database_readiness_probe import DatabaseReadinessProbe


@pytest.fixture
def session() -> MagicMock:
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    return session


@pytest.fixture
def sut(session: MagicMock) -> DatabaseReadinessProbe:
    return DatabaseReadinessProbe(session)


def test_should_be_named_database(sut: DatabaseReadinessProbe) -> None:
    assert sut.name == "database"


async def test_should_be_ready_when_the_database_answers(
    sut: DatabaseReadinessProbe, session: MagicMock
) -> None:
    assert await sut.is_ready() is True
    statement = session.execute.await_args.args[0]
    assert str(statement) == "SELECT 1"


@pytest.mark.parametrize(
    "error",
    [
        OperationalError("SELECT 1", {}, Exception("down")),
        ConnectionRefusedError("refused"),
    ],
)
async def test_should_not_be_ready_when_the_database_fails(
    sut: DatabaseReadinessProbe, session: MagicMock, error: Exception
) -> None:
    session.execute.side_effect = error
    assert await sut.is_ready() is False


async def test_should_not_be_ready_when_the_database_hangs(
    sut: DatabaseReadinessProbe, session: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(probe_module, "READINESS_TIMEOUT_SECONDS", 0.01)

    async def hang(*_: object) -> None:
        await asyncio.sleep(1)

    session.execute.side_effect = hang
    assert await sut.is_ready() is False
