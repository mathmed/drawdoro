import json
from collections import Counter
from pathlib import Path

import pytest

from scripts import suppressions
from scripts.suppressions import Change, Comparison, Kind, Occurrence, scan_python, scan_typescript

HANDLER = "app/handler.py"
COMPONENT = "frontend/src/Component.tsx"


def python_kinds(source: str) -> list[Kind]:
    return [occurrence.kind for occurrence in scan_python("x.py", source)]


def typescript_kinds(source: str) -> list[Kind]:
    return [occurrence.kind for occurrence in scan_typescript("x.ts", source)]


def write(root: Path, relative: str, source: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    return path


class TestPythonComments:
    @pytest.mark.parametrize(
        ("comment", "kind"),
        [
            ("# noqa", Kind.NOQA),
            ("# noqa: E501", Kind.NOQA),
            ("# ruff: noqa", Kind.NOQA),
            ("# type: ignore", Kind.TYPE_IGNORE),
            ("# type: ignore[arg-type]", Kind.TYPE_IGNORE),
            ("# nosec B101", Kind.NOSEC),
            ("# pragma: no cover", Kind.NO_COVER),
            ("# pragma: no branch", Kind.NO_COVER),
            ("# pylint: disable=invalid-name", Kind.PYLINT),
            ("# mypy: ignore-errors", Kind.MYPY),
            ("# pyright: ignore[reportGeneralTypeIssues]", Kind.PYRIGHT),
            ("# fmt: off", Kind.FORMATTER),
            ("# fmt: skip", Kind.FORMATTER),
            ("# isort: skip_file", Kind.FORMATTER),
        ],
    )
    def test_should_detect_each_comment_suppression(self, comment: str, kind: Kind) -> None:
        assert python_kinds(f"value = 1  {comment}\n") == [kind]

    def test_should_count_every_suppression_in_the_same_comment(self) -> None:
        assert python_kinds("value = 1  # type: ignore[misc]  # noqa: E501\n") == [
            Kind.NOQA,
            Kind.TYPE_IGNORE,
        ]

    def test_should_report_the_line_of_the_comment(self) -> None:
        occurrences = scan_python(HANDLER, "a = 1\n\nb = 2  # nosec\n")

        assert occurrences == [Occurrence(HANDLER, 3, Kind.NOSEC)]

    @pytest.mark.parametrize(
        "source",
        [
            'text = "# noqa"\n',
            'text = """\n# type: ignore\n"""\n',
            "# a regular comment about types\n",
            "skip = True\nif skip:\n    pass\n",
        ],
    )
    def test_should_ignore_text_that_is_not_a_suppression(self, source: str) -> None:
        assert python_kinds(source) == []


class TestPythonTestMarkers:
    @pytest.mark.parametrize(
        ("source", "kind"),
        [
            ("import pytest\n@pytest.mark.skip\ndef f(): ...\n", Kind.TEST_SKIP),
            (
                "import pytest\n@pytest.mark.skipif(True, reason='x')\ndef f(): ...\n",
                Kind.TEST_SKIP,
            ),
            ("import pytest\n@pytest.mark.xfail\ndef f(): ...\n", Kind.TEST_XFAIL),
            ("from pytest import mark\n@mark.skip\ndef f(): ...\n", Kind.TEST_SKIP),
            ("import pytest\npytestmark = pytest.mark.skip\n", Kind.TEST_SKIP),
            ("import pytest\ndef f():\n    pytest.skip('x')\n", Kind.TEST_SKIP),
            ("import pytest\nyaml = pytest.importorskip('yaml')\n", Kind.TEST_SKIP),
            ("import pytest\ndef f():\n    pytest.xfail('x')\n", Kind.TEST_XFAIL),
            ("import pytest\np = pytest.param(1, marks=pytest.mark.xfail)\n", Kind.TEST_XFAIL),
            ("from pytest import skip as s\ndef f():\n    s('x')\n", Kind.TEST_SKIP),
            ("import unittest\n@unittest.skipIf(True, 'x')\ndef f(): ...\n", Kind.TEST_SKIP),
            ("import unittest\n@unittest.expectedFailure\ndef f(): ...\n", Kind.TEST_XFAIL),
            ("def test(self):\n    self.skipTest('x')\n", Kind.TEST_SKIP),
        ],
    )
    def test_should_detect_skipped_and_expected_failure_tests(
        self, source: str, kind: Kind
    ) -> None:
        assert python_kinds(source) == [kind]

    def test_should_not_count_other_pytest_marks(self) -> None:
        source = "import pytest\n@pytest.mark.parametrize('a', [1])\ndef f(a): ...\n"

        assert python_kinds(source) == []

    def test_should_not_count_names_that_were_not_imported_from_pytest(self) -> None:
        assert python_kinds("from helpers import skip\nskip('x')\n") == []

    def test_should_fail_loudly_on_invalid_python(self) -> None:
        with pytest.raises(SyntaxError):
            scan_python("x.py", "def broken(:\n")


class TestTypescriptComments:
    @pytest.mark.parametrize(
        ("line", "kind"),
        [
            ("// eslint-disable-next-line react-hooks/exhaustive-deps", Kind.ESLINT_DISABLE),
            ("const a = 1 // eslint-disable-line no-console", Kind.ESLINT_DISABLE),
            ("/* eslint-disable */", Kind.ESLINT_DISABLE),
            ("{/* eslint-disable-line */}", Kind.ESLINT_DISABLE),
            ('/* eslint no-console: "off" */', Kind.ESLINT_DISABLE),
            ("// @ts-ignore", Kind.TS_IGNORE),
            ("// @ts-expect-error the library types are wrong", Kind.TS_EXPECT_ERROR),
            ("// @ts-nocheck", Kind.TS_NOCHECK),
            ("/* istanbul ignore next */", Kind.NO_COVER),
            ("/* v8 ignore next 3 */", Kind.NO_COVER),
            ("/* c8 ignore start */", Kind.NO_COVER),
            ("// prettier-ignore", Kind.FORMATTER),
        ],
    )
    def test_should_detect_each_comment_directive(self, line: str, kind: Kind) -> None:
        assert typescript_kinds(f"{line}\n") == [kind]

    @pytest.mark.parametrize(
        "source",
        [
            "// keep eslint happy without disabling anything\n",
            "const eslint = 'eslint-disable'\n",
            "/* eslint-env browser */\n",
            "// ts-ignore is not used here\n",
        ],
    )
    def test_should_ignore_text_that_is_not_a_directive(self, source: str) -> None:
        assert typescript_kinds(source) == []

    def test_should_report_the_line_of_the_directive(self) -> None:
        occurrences = scan_typescript(COMPONENT, "const a = 1\n// @ts-ignore\nuse(a)\n")

        assert occurrences == [Occurrence(COMPONENT, 2, Kind.TS_IGNORE)]


class TestTypescriptTestMarkers:
    @pytest.mark.parametrize(
        ("line", "kind"),
        [
            ("it.skip('renders', () => {})", Kind.TEST_SKIP),
            ("test.skip('renders', () => {})", Kind.TEST_SKIP),
            ("describe.skip('Panel', () => {})", Kind.TEST_SKIP),
            ("it.skipIf(isCi)('renders', () => {})", Kind.TEST_SKIP),
            ("it.runIf(isLinux)('renders', () => {})", Kind.TEST_SKIP),
            ("it.todo('renders')", Kind.TEST_SKIP),
            ("describe.concurrent.skip('Panel', () => {})", Kind.TEST_SKIP),
            ("it.skip.each([1, 2])('renders %s', () => {})", Kind.TEST_SKIP),
            ("ctx.skip()", Kind.TEST_SKIP),
            ("xit('renders', () => {})", Kind.TEST_SKIP),
            ("xdescribe('Panel', () => {})", Kind.TEST_SKIP),
            ("it.only('renders', () => {})", Kind.TEST_ONLY),
            ("describe.only('Panel', () => {})", Kind.TEST_ONLY),
            ("fit('renders', () => {})", Kind.TEST_ONLY),
            ("fdescribe('Panel', () => {})", Kind.TEST_ONLY),
            ("it.fails('throws', () => {})", Kind.TEST_XFAIL),
        ],
    )
    def test_should_detect_skipped_focused_and_failing_tests(self, line: str, kind: Kind) -> None:
        assert typescript_kinds(f"{line}\n") == [kind]

    @pytest.mark.parametrize(
        "source",
        [
            "it('skips nothing', () => {})\n",
            "describe.each([1, 2])('Panel %s', () => {})\n",
            "editor.zoomToFit()\n",
            "layout.fit(bounds)\n",
            "const skip = list.skip(2)\n",
        ],
    )
    def test_should_ignore_regular_tests_and_lookalike_calls(self, source: str) -> None:
        assert typescript_kinds(source) == []


class TestScan:
    def test_should_scan_python_and_typescript_files_under_every_root(self, tmp_path: Path) -> None:
        write(tmp_path, "app/a.py", "a = 1  # noqa\n")
        write(tmp_path, "frontend/src/b.test.tsx", "it.only('x', () => {})\n")
        write(tmp_path, "frontend/vite.config.ts", "// @ts-nocheck\n")
        write(tmp_path, "app/notes.md", "# noqa\n")

        occurrences = suppressions.scan([tmp_path / "app", tmp_path / "frontend"])

        assert [(Path(item.path).name, item.kind) for item in occurrences] == [
            ("a.py", Kind.NOQA),
            ("b.test.tsx", Kind.TEST_ONLY),
            ("vite.config.ts", Kind.TS_NOCHECK),
        ]

    @pytest.mark.parametrize(
        "relative",
        [
            "frontend/node_modules/lib/index.js",
            "frontend/dist/assets/index.js",
            "frontend/coverage/prettify.js",
            "mcp/.venv/lib/site.py",
            "app/__pycache__/a.py",
        ],
    )
    def test_should_skip_installed_packages_caches_and_build_output(
        self, tmp_path: Path, relative: str
    ) -> None:
        root = tmp_path / relative.split("/")[0]
        source = "// eslint-disable\n" if relative.endswith(".js") else "a = 1  # noqa\n"
        write(tmp_path, relative, source)

        assert suppressions.scan([root]) == ()

    def test_should_fail_when_a_root_does_not_exist(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="root not found"):
            suppressions.scan([tmp_path / "missing"])

    def test_should_cover_the_api_mcp_scripts_tests_and_frontend_by_default(self) -> None:
        assert [root.as_posix() for root in suppressions.DEFAULT_ROOTS] == [
            "app",
            "alembic",
            "mcp",
            "scripts",
            "tests",
            "frontend",
        ]


class TestComparison:
    @pytest.fixture
    def sut(self) -> Comparison:
        occurrences = (
            Occurrence(HANDLER, 3, Kind.NOSEC),
            Occurrence(HANDLER, 9, Kind.NOSEC),
            Occurrence("tests/t.py", 1, Kind.TEST_SKIP),
        )
        baseline = Counter({(HANDLER, Kind.NOSEC): 1, ("app/gone.py", Kind.NOQA): 2})
        return Comparison(occurrences, baseline)

    def test_should_list_increases_with_every_line_of_that_kind_in_the_file(
        self, sut: Comparison
    ) -> None:
        assert sut.increases == (
            Change(HANDLER, Kind.NOSEC, 1, 2, (3, 9)),
            Change("tests/t.py", Kind.TEST_SKIP, 0, 1, (1,)),
        )

    def test_should_list_decreases_including_files_that_no_longer_exist(
        self, sut: Comparison
    ) -> None:
        assert sut.decreases == (Change("app/gone.py", Kind.NOQA, 2, 0, ()),)

    def test_should_have_no_changes_when_counts_match(self) -> None:
        occurrences = (Occurrence(HANDLER, 3, Kind.NOSEC),)

        comparison = Comparison(occurrences, Counter({(HANDLER, Kind.NOSEC): 1}))

        assert comparison.changes == ()

    def test_should_count_a_moved_suppression_as_an_increase(self) -> None:
        occurrences = (Occurrence("app/other.py", 1, Kind.NOSEC),)

        comparison = Comparison(occurrences, Counter({(HANDLER, Kind.NOSEC): 1}))

        assert [change.path for change in comparison.increases] == ["app/other.py"]
        assert [change.path for change in comparison.decreases] == [HANDLER]

    def test_should_serialize_the_result_line(self, sut: Comparison) -> None:
        line = sut.to_result_line()

        payload = json.loads(line.removeprefix(suppressions.RESULT_PREFIX))
        assert line.startswith(suppressions.RESULT_PREFIX)
        assert payload["total"] == 3
        assert payload["baseline_total"] == 3
        assert payload["totals"] == {"nosec": 2, "test-skip": 1}
        assert payload["changes"][0] == {
            "path": "app/gone.py",
            "kind": "noqa",
            "baseline": 2,
            "current": 0,
            "lines": [],
        }


class TestBaseline:
    def test_should_treat_a_missing_baseline_as_empty(self, tmp_path: Path) -> None:
        assert suppressions.load_baseline(tmp_path / "missing.json") == Counter()

    def test_should_round_trip_the_baseline(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        counts = Counter({(HANDLER, Kind.NOSEC): 1, (COMPONENT, Kind.ESLINT_DISABLE): 2})

        suppressions.write_baseline(path, counts)

        assert suppressions.load_baseline(path) == counts
        assert json.loads(path.read_text()) == {
            HANDLER: {"nosec": 1},
            COMPONENT: {"eslint-disable": 2},
        }

    def test_should_reject_an_unknown_kind(self, tmp_path: Path) -> None:
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps({HANDLER: {"unknown": 1}}))

        with pytest.raises(ValueError, match="unknown"):
            suppressions.load_baseline(path)


class TestCommands:
    @pytest.fixture
    def root(self, tmp_path: Path) -> Path:
        write(tmp_path, "app/a.py", "a = 1  # noqa\nb = 2  # noqa\n")
        return tmp_path / "app"

    @pytest.fixture
    def baseline(self, tmp_path: Path) -> Path:
        return tmp_path / "baseline.json"

    def run(self, baseline: Path, root: Path, *command: str) -> int:
        return suppressions.main(["--baseline", str(baseline), "--root", str(root), *command])

    def lock(self, baseline: Path, root: Path, count: int) -> None:
        file = (root / "a.py").as_posix()
        suppressions.write_baseline(baseline, Counter({(file, Kind.NOQA): count}))

    def test_should_pass_when_suppressions_match_the_baseline(
        self, baseline: Path, root: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        self.lock(baseline, root, 2)

        with caplog.at_level("INFO"):
            assert self.run(baseline, root, "check") == 0
        assert "Suppressions match the baseline." in caplog.text

    def test_should_print_the_result_line_for_the_quality_report(
        self, baseline: Path, root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        self.lock(baseline, root, 2)

        self.run(baseline, root, "check")

        line = capsys.readouterr().out.strip().splitlines()[-1]
        assert json.loads(line.removeprefix(suppressions.RESULT_PREFIX))["total"] == 2

    def test_should_fail_when_a_suppression_is_added(
        self, baseline: Path, root: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        self.lock(baseline, root, 1)

        with caplog.at_level("INFO"):
            assert self.run(baseline, root, "check") == 1
        assert "New suppressions" in caplog.text
        assert "noqa 1 -> 2 (lines: 1, 2)" in caplog.text

    def test_should_fail_when_the_baseline_is_stale(
        self, baseline: Path, root: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        self.lock(baseline, root, 3)

        with caplog.at_level("INFO"):
            assert self.run(baseline, root, "check") == 1
        assert "make suppressions-update" in caplog.text

    def test_should_lower_the_baseline_on_update(self, baseline: Path, root: Path) -> None:
        self.lock(baseline, root, 3)

        assert self.run(baseline, root, "update") == 0
        assert self.run(baseline, root, "check") == 0

    def test_should_refuse_to_raise_the_baseline_without_the_flag(
        self, baseline: Path, root: Path
    ) -> None:
        self.lock(baseline, root, 1)

        assert self.run(baseline, root, "update") == 1
        assert self.run(baseline, root, "check") == 1

    def test_should_raise_the_baseline_with_the_flag(self, baseline: Path, root: Path) -> None:
        self.lock(baseline, root, 1)

        assert self.run(baseline, root, "update", "--allow-increase") == 0
        assert self.run(baseline, root, "check") == 0
