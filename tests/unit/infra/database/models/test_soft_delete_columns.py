import pytest
from sqlalchemy import Column, DateTime

from app.infra.database.models.diagram import DiagramORM
from app.infra.database.models.folder import FolderORM
from app.infra.database.models.project import ProjectORM
from app.infra.database.models.workspace import Base, WorkspaceORM


@pytest.fixture(params=[WorkspaceORM, ProjectORM, FolderORM, DiagramORM])
def sut(request: pytest.FixtureRequest) -> type[Base]:
    model: type[Base] = request.param
    return model


def test_should_store_soft_delete_timestamps_with_time_zone(sut: type[Base]) -> None:
    column = sut.__table__.c.deleted_at
    assert isinstance(column, Column)
    assert isinstance(column.type, DateTime)
    assert column.type.timezone is True
    assert column.nullable is True
