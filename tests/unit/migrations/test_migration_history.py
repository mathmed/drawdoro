from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def sut() -> ScriptDirectory:
    return ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))


# Two heads make `alembic upgrade head` fail on deploy.
def test_should_have_a_single_head(sut: ScriptDirectory) -> None:
    assert len(sut.get_heads()) == 1


def test_should_chain_every_revision_down_to_a_single_base(sut: ScriptDirectory) -> None:
    revisions = list(sut.walk_revisions())
    assert [r.revision for r in revisions if r.down_revision is None] == ["0001"]
    known = {r.revision for r in revisions}
    assert all(r.down_revision in known for r in revisions if r.down_revision is not None)


def test_should_add_comment_resolution_on_top_of_the_history_and_api_keys(
    sut: ScriptDirectory,
) -> None:
    revision = sut.get_revision("0007")
    assert revision is not None
    assert revision.down_revision == "0006"
