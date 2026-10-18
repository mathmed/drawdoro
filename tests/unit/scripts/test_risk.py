import io
from pathlib import Path

import pytest

from scripts import risk
from scripts.risk import Assessment, Floor, FloorHit, RiskFloorError, RiskLevel


@pytest.fixture
def floors() -> tuple[Floor, ...]:
    return risk.load_floors(risk.DEFAULT_FLOORS)


class TestCommittedFloors:
    @pytest.mark.parametrize(
        ("file", "category"),
        [
            ("pyproject.toml", "pipeline config"),
            ("uv.lock", "pipeline config"),
            ("mcp/pyproject.toml", "pipeline config"),
            (".pre-commit-config.yaml", "pipeline config"),
            ("Makefile", "pipeline config"),
            ("suppressions-baseline.json", "pipeline config"),
            ("contract-baseline.json", "pipeline config"),
            ("scripts/quality_report.py", "pipeline config"),
            ("scripts/smoke.sh", "pipeline config"),
            (".github/workflows/ci.yml", "pipeline config"),
            (".github/risk-floors.yaml", "pipeline config"),
            (".claude/agents/coder.md", "pipeline config"),
            ("CLAUDE.md", "pipeline config"),
            ("docker/Dockerfile", "pipeline config"),
            ("frontend/package.json", "pipeline config"),
            ("frontend/vitest.config.ts", "pipeline config"),
            ("frontend/eslint.config.js", "pipeline config"),
            ("frontend/tsconfig.json", "pipeline config"),
            ("alembic/versions/0012_add_column.py", "migrations"),
            ("alembic/env.py", "migrations"),
            ("alembic.ini", "migrations"),
            ("app/infra/database/models/diagram.py", "migrations"),
            ("app/infra/auth/cognito_token_verifier.py", "auth"),
            ("app/domain/usecases/auth/authenticate_user.py", "auth"),
            ("app/domain/usecases/api_key/create_api_key.py", "auth"),
            ("app/domain/services/api_key_secret.py", "auth"),
            ("app/domain/usecases/diagram/share_diagram.py", "auth"),
            ("app/presentation/fastapi/routes/share_routes.py", "auth"),
            ("app/presentation/fastapi/dependencies/current_user.py", "auth"),
            ("app/presentation/fastapi/dependencies/workspace_access.py", "auth"),
            ("app/presentation/fastapi/configs/configs.py", "auth"),
            ("app/presentation/fastapi/routes/__init__.py", "auth"),
            ("app/presentation/fastapi/routes/websocket_routes.py", "auth"),
            ("app/domain/services/gallery_ownership.py", "auth"),
            ("app/domain/usecases/workspace_member/add_workspace_member.py", "auth"),
            ("app/common/settings.py", "auth"),
            ("mcp/caller_key.py", "auth"),
            ("mcp/settings.py", "auth"),
            ("frontend/src/auth/session.ts", "auth"),
            ("frontend/src/store/useAuthStore.ts", "auth"),
            ("frontend/src/components/account/ApiKeysDialog.tsx", "auth"),
            ("frontend/src/components/diagram/ShareDialog.tsx", "auth"),
            ("frontend/src/api/client.ts", "auth"),
        ],
    )
    def test_should_put_sensitive_files_at_high(
        self, floors: tuple[Floor, ...], file: str, category: str
    ) -> None:
        assessment = risk.assess([file], floors)

        assert assessment.floor == RiskLevel.HIGH
        assert category in [hit.category for hit in assessment.hits]

    @pytest.mark.parametrize(
        "file",
        [
            "app/domain/usecases/diagram/create_diagram.py",
            "app/presentation/fastapi/routes/diagram_routes.py",
            "tests/unit/domain/services/test_canvas_geometry.py",
            "frontend/src/components/canvas/DrawingCanvas.tsx",
            "mcp/tools/diagrams.py",
            "docs/FEATURES.md",
            "README.md",
        ],
    )
    def test_should_leave_ordinary_files_at_low(self, floors: tuple[Floor, ...], file: str) -> None:
        assert risk.assess([file], floors).floor == RiskLevel.LOW


class TestAssessment:
    @pytest.fixture
    def sut(self) -> Assessment:
        floors = (
            Floor("docs", RiskLevel.MEDIUM, ("docs/**",)),
            Floor("pipeline", RiskLevel.HIGH, ("Makefile",)),
            Floor("unused", RiskLevel.CRITICAL, ("never/**",)),
        )
        return risk.assess(["docs/a.md", "Makefile", "docs/b.md", "app/x.py"], floors)

    def test_should_group_matching_files_by_category(self, sut: Assessment) -> None:
        assert sut.hits == (
            FloorHit("docs", RiskLevel.MEDIUM, ("docs/a.md", "docs/b.md")),
            FloorHit("pipeline", RiskLevel.HIGH, ("Makefile",)),
        )

    def test_should_take_the_highest_level_as_the_floor(self, sut: Assessment) -> None:
        assert sut.floor == RiskLevel.HIGH

    def test_should_describe_the_floor_and_the_files(self, sut: Assessment) -> None:
        assert sut.describe() == (
            "Risk floor: high\n- docs (medium): docs/a.md, docs/b.md\n- pipeline (high): Makefile"
        )

    def test_should_be_low_without_hits(self) -> None:
        assessment = Assessment(())

        assert assessment.floor == RiskLevel.LOW
        assert assessment.describe().endswith("no file matches a floor category")

    def test_should_match_files_at_the_root_with_a_double_star_pattern(self) -> None:
        floor = Floor("auth", RiskLevel.HIGH, ("**/*auth*",))

        assert floor.matches("auth.py")
        assert floor.matches("app/x/auth_routes.py")
        assert not floor.matches("app/x/Authorization.py")


class TestLoadFloors:
    def write(self, tmp_path: Path, content: str) -> Path:
        path = tmp_path / "floors.yaml"
        path.write_text(content)
        return path

    def test_should_load_floors(self, tmp_path: Path) -> None:
        path = self.write(tmp_path, "floors:\n  - {category: x, level: medium, paths: [a/**]}\n")

        assert risk.load_floors(path) == (Floor("x", RiskLevel.MEDIUM, ("a/**",)),)

    @pytest.mark.parametrize(
        ("content", "message"),
        [
            ("[]", "top-level `floors` list"),
            ("floors: [x]", "must be a mapping"),
            ("floors:\n  - {category: x, level: high, paths: []}", "non-empty list of paths"),
            ("floors:\n  - {category: x, level: high}", "non-empty list of paths"),
            ("floors:\n  - {level: high, paths: [a]}", "needs a category"),
            ("floors:\n  - {category: x, level: urgent, paths: [a]}", "unknown level 'urgent'"),
        ],
    )
    def test_should_reject_invalid_files(self, tmp_path: Path, content: str, message: str) -> None:
        with pytest.raises(RiskFloorError, match=message):
            risk.load_floors(self.write(tmp_path, content))


class TestChangedFiles:
    def test_should_deduplicate_sort_and_drop_blank_lines(self) -> None:
        text = "Makefile\n\nREADME.md\n  Makefile  \n"

        assert risk.parse_changed_files(text) == ["Makefile", "README.md"]

    def test_should_read_the_changed_files_from_stdin(self) -> None:
        assert risk.read_changed_files("-", io.StringIO("b.py\na.py\n")) == ["a.py", "b.py"]

    def test_should_read_the_changed_files_from_a_file(self, tmp_path: Path) -> None:
        path = tmp_path / "changed.txt"
        path.write_text("a.py\n")

        assert risk.read_changed_files(str(path), io.StringIO("ignored\n")) == ["a.py"]


class TestLabels:
    @pytest.mark.parametrize(
        ("labels", "floor", "problem"),
        [
            (["risk:high"], RiskLevel.HIGH, None),
            (["bug", "risk:critical"], RiskLevel.HIGH, None),
            (["risk:low"], RiskLevel.LOW, None),
            (
                ["risk:medium"],
                RiskLevel.HIGH,
                "risk:medium is below the floor of this PR (risk:high)",
            ),
            ([], RiskLevel.LOW, "expected exactly one risk label"),
            (["risk:low", "risk:high"], RiskLevel.LOW, "expected exactly one risk label"),
            (["risk:urgent"], RiskLevel.LOW, "unknown risk label risk:urgent"),
        ],
    )
    def test_should_require_one_known_label_at_or_above_the_floor(
        self, labels: list[str], floor: RiskLevel, problem: str | None
    ) -> None:
        result = risk.label_problem(labels, floor)

        if problem is None:
            assert result is None
        else:
            assert result is not None
            assert problem in result

    def test_should_parse_the_labels_of_the_event(self) -> None:
        assert risk.parse_labels('["risk:low", "bug"]') == ["risk:low", "bug"]
        assert risk.parse_labels("") == []

    @pytest.mark.parametrize("labels_json", ['{"a": 1}', "[1]"])
    def test_should_reject_labels_that_are_not_a_list_of_strings(self, labels_json: str) -> None:
        with pytest.raises(RiskFloorError, match="JSON list of strings"):
            risk.parse_labels(labels_json)


class TestCommands:
    @pytest.fixture
    def sut(self) -> io.StringIO:
        return io.StringIO("Makefile\nREADME.md\n")

    def test_should_print_the_floor(
        self, sut: io.StringIO, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level("INFO"):
            assert risk.main(["--changed-files", "-", "floor"], sut) == 0
        assert "Risk floor: high\n- pipeline config (high): Makefile" in caplog.text

    def test_should_pass_with_a_label_at_the_floor(
        self, sut: io.StringIO, caplog: pytest.LogCaptureFixture
    ) -> None:
        argv = ["--changed-files", "-", "check", "--labels-json", '["risk:high"]']

        with caplog.at_level("INFO"):
            assert risk.main(argv, sut) == 0
        assert "at or above the floor" in caplog.text

    def test_should_fail_with_a_label_below_the_floor(
        self, sut: io.StringIO, caplog: pytest.LogCaptureFixture
    ) -> None:
        argv = ["--changed-files", "-", "check", "--labels-json", '["risk:low"]']

        assert risk.main(argv, sut) == 1
        assert "risk:low is below the floor" in caplog.text

    @pytest.mark.parametrize(
        "argv",
        [
            ["--changed-files", "missing.txt", "floor"],
            ["--changed-files", "-", "check", "--labels-json", "not json"],
            ["--changed-files", "-", "--floors", "missing.yaml", "floor"],
        ],
    )
    def test_should_fail_loudly_on_unreadable_input(
        self, sut: io.StringIO, caplog: pytest.LogCaptureFixture, argv: list[str]
    ) -> None:
        assert risk.main(argv, sut) == 1
        assert "Risk label check failed" in caplog.text
