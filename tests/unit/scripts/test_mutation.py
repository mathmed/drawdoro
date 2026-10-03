import json
import subprocess
from pathlib import Path

import pytest

from scripts import mutation, quality_report
from scripts.mutation import (
    ChangedReport,
    Outcome,
    Tally,
    collect,
    in_scope,
    load_scope,
    location_of,
    merge,
    overall,
    parse_changed_lines,
    targets_for_file,
)

SOURCE = """import uuid

from app.domain.errors import NotFoundError

LIMIT = 3


class CreateThing:
    def __init__(self, repo: object) -> None:
        self._repo = repo

    async def execute(self, value: int) -> int:
        if value > LIMIT:
            raise NotFoundError("x")
        return value


@decorated
def helper(value: int) -> int:
    return value + 1
"""
MODULE = "app.domain.usecases.thing.create_thing"
FILE = "app/domain/usecases/thing/create_thing.py"
SCOPE = ["app/domain/usecases/*", "app/domain/services/*"]


def write_meta(mutants_dir: Path, module: str, exit_codes: dict[str, int | None]) -> None:
    path = mutants_dir / f"{module}.meta"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"exit_code_by_key": exit_codes}))


class TestChangedLines:
    def test_should_read_added_and_changed_lines_from_hunks(self) -> None:
        diff = "@@ -10,2 +12,3 @@ def x\n+a\n@@ -40 +44 @@\n-b\n+c\n"

        assert parse_changed_lines(diff) == {12, 13, 14, 44}

    def test_should_mark_both_neighbours_of_a_deletion(self) -> None:
        assert parse_changed_lines("@@ -5,2 +4,0 @@\n-a\n-b\n") == {4, 5}


class TestTargetsForFile:
    def test_should_target_only_the_changed_method(self) -> None:
        assert targets_for_file(FILE, SOURCE, {14}) == [f"{MODULE}.xǁCreateThingǁexecute__mutmut_*"]

    def test_should_target_a_top_level_function_including_its_decorator(self) -> None:
        assert targets_for_file(FILE, SOURCE, {18}) == [f"{MODULE}.x_helper__mutmut_*"]

    def test_should_target_the_whole_file_when_a_constant_changes(self) -> None:
        assert targets_for_file(FILE, SOURCE, {5, 14}) == [f"{MODULE}.*"]

    def test_should_target_the_whole_file_when_every_function_changed(self) -> None:
        assert targets_for_file(FILE, SOURCE, {10, 13, 20}) == [f"{MODULE}.*"]

    def test_should_ignore_imports_blank_lines_and_comments(self) -> None:
        assert targets_for_file(FILE, SOURCE, {1, 2, 3, 4}) == []


class TestScope:
    @pytest.mark.parametrize(
        ("file", "expected"),
        [
            ("app/domain/usecases/thing/create_thing.py", True),
            ("app/domain/services/revision_recorder.py", True),
            ("app/domain/usecases/thing/__init__.py", False),
            ("app/domain/entities/thing.py", False),
            ("app/infra/database/repo.py", False),
            ("app/domain/usecases/README.md", False),
        ],
    )
    def test_should_only_accept_python_files_matched_by_only_mutate(
        self, file: str, expected: bool
    ) -> None:
        assert in_scope(file, SCOPE) is expected

    def test_should_read_the_scope_from_pyproject(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.mutmut]\nsource_paths = ["app/"]\nonly_mutate = ["app/x/*"]\n')

        assert load_scope(pyproject) == ["app/x/*"]

    def test_should_use_the_project_scope(self) -> None:
        assert load_scope() == SCOPE


class TestCollect:
    @pytest.fixture
    def sut(self, tmp_path: Path) -> Path:
        write_meta(
            tmp_path,
            "app/domain/usecases/thing/create_thing.py",
            {
                f"{MODULE}.xǁCreateThingǁexecute__mutmut_1": 1,
                f"{MODULE}.xǁCreateThingǁexecute__mutmut_2": 0,
                f"{MODULE}.xǁCreateThingǁ__init____mutmut_1": 33,
                f"{MODULE}.x_helper__mutmut_1": 36,
            },
        )
        write_meta(
            tmp_path,
            "app/domain/services/other.py",
            {"app.domain.services.other.x_f__mutmut_1": None},
        )
        return tmp_path

    def test_should_score_timeouts_as_killed_and_no_tests_as_survivors(self, sut: Path) -> None:
        tally = collect(sut)[FILE]

        assert (tally.total, tally.detected, tally.score) == (4, 2, 50.0)
        assert tally.counts[Outcome.NO_TESTS] == 1
        assert len(tally.survivors) == 2

    def test_should_keep_only_the_mutants_matching_the_targets(self, sut: Path) -> None:
        tallies = collect(sut, [f"{MODULE}.xǁCreateThingǁexecute__mutmut_*"])

        assert list(tallies) == [FILE]
        assert tallies[FILE].total == 2

    def test_should_count_unchecked_mutants_as_not_killed(self, sut: Path) -> None:
        tally = collect(sut)["app/domain/services/other.py"]

        assert (tally.counts[Outcome.OTHER], tally.score) == (1, 0.0)

    def test_should_group_use_cases_by_package(self, sut: Path) -> None:
        packages = merge(collect(sut), "")

        assert set(packages) == {"app/domain/usecases/thing", "app/domain/services/other.py"}
        assert overall(collect(sut)).total == 5

    def test_should_render_the_full_report(
        self, sut: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(mutation, "diff_of", lambda _: "-a\n+b")

        report = mutation.full_report(collect(sut), diffs_per_module=1)

        assert report.startswith("## Mutation testing\n\n**Score: 40.0%**")
        assert "### By package" in report
        assert "... and 1 more" in report


class TestLocation:
    def test_should_locate_a_method(self) -> None:
        assert location_of(f"{MODULE}.xǁCreateThingǁexecute__mutmut_3") == (
            FILE,
            "CreateThing.execute",
        )

    def test_should_locate_a_function(self) -> None:
        assert location_of(f"{MODULE}.x_helper__mutmut_1") == (FILE, "helper")

    def test_should_keep_unknown_names(self) -> None:
        assert location_of("weird") == ("weird", "weird")


class TestChangedReport:
    @pytest.fixture
    def sut(self, monkeypatch: pytest.MonkeyPatch) -> ChangedReport:
        monkeypatch.setattr(mutation, "diff_of", lambda _: "-    a\n+    b")
        tally = Tally()
        tally.add(f"{MODULE}.xǁCreateThingǁexecute__mutmut_1", Outcome.KILLED)
        tally.add(f"{MODULE}.xǁCreateThingǁexecute__mutmut_2", Outcome.SURVIVED)
        return ChangedReport({FILE: tally}, 60.0, [f"{MODULE}.*"])

    def test_should_fail_below_the_ratchet(self, sut: ChangedReport) -> None:
        assert (sut.total.score, sut.passed) == (50.0, False)

    def test_should_render_markdown_with_the_survivors(self, sut: ChangedReport) -> None:
        markdown = sut.to_markdown()

        assert "**Score: 50.0%** (ratchet 60.0%, ❌ below the ratchet)" in markdown
        assert f"- `{MODULE}.xǁCreateThingǁexecute__mutmut_2`" in markdown

    def test_should_produce_a_result_line_the_quality_report_understands(
        self, sut: ChangedReport
    ) -> None:
        line = sut.to_result_line()
        fragment = quality_report.Fragment(quality_report.Analysis.MUTATION, 1, f"x\n{line}\n")

        finding = quality_report.analyze_mutation(fragment)

        assert finding.status == quality_report.Status.FAILED
        assert finding.summary.startswith("score 50.0% (ratchet 60%) · 1 of 2 mutants killed")
        assert "`CreateThing.execute`" in finding.details
        assert "```diff\n-    a\n+    b\n```" in finding.details

    def test_should_produce_a_skipped_line_the_quality_report_understands(self) -> None:
        line = mutation.skipped_result_line(60.0, "Nothing changed.")
        fragment = quality_report.Fragment(quality_report.Analysis.MUTATION, 0, line)

        finding = quality_report.analyze_mutation(fragment)

        assert (finding.status, finding.summary) == (
            quality_report.Status.SKIPPED,
            "Nothing changed.",
        )


class TestChangedCommand:
    @pytest.fixture
    def sut(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
        monkeypatch.setenv("MUTATION_MIN_SCORE", "60")
        monkeypatch.setattr(mutation, "changed_targets", lambda base, scope: [f"{MODULE}.*"])
        monkeypatch.setattr(mutation, "diff_of", lambda _: None)
        return summary

    def test_should_skip_when_no_scoped_file_changed(
        self, sut: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(mutation, "changed_targets", lambda base, scope: [])

        assert mutation.changed_command("origin/main") == 0
        assert '"skipped": true' in capsys.readouterr().out
        assert "nothing to mutate" in sut.read_text()

    def test_should_skip_when_the_changed_functions_have_no_mutants(
        self, sut: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(mutation, "run_mutmut", lambda _: (1, mutation.NOTHING_MATCHED))

        assert mutation.changed_command("origin/main") == 0
        assert "produce no mutants" in capsys.readouterr().out

    def test_should_propagate_a_mutmut_failure(
        self, sut: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(mutation, "run_mutmut", lambda _: (2, "clean tests failed"))

        assert mutation.changed_command("origin/main") == 2

    @pytest.mark.parametrize(("outcome", "exit_code"), [(Outcome.KILLED, 0), (Outcome.SURVIVED, 1)])
    def test_should_gate_on_the_ratchet(
        self,
        sut: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        outcome: Outcome,
        exit_code: int,
    ) -> None:
        tally = Tally()
        tally.add(f"{MODULE}.x_helper__mutmut_1", outcome)
        monkeypatch.setattr(mutation, "run_mutmut", lambda _: (0, ""))
        monkeypatch.setattr(mutation, "collect", lambda _, patterns: {FILE: tally})

        assert mutation.changed_command("origin/main") == exit_code
        assert mutation.RESULT_PREFIX in capsys.readouterr().out
        assert "Mutation testing (changed domain code)" in sut.read_text()


class TestReportCommand:
    def test_should_fail_without_results(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(mutation, "MUTANTS_DIR", tmp_path)

        assert mutation.report_command(10, 0.0) == 1

    def test_should_fail_below_the_minimum_score(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        write_meta(tmp_path, FILE, {f"{MODULE}.x_helper__mutmut_1": 0})
        monkeypatch.setattr(mutation, "MUTANTS_DIR", tmp_path)
        monkeypatch.setattr(mutation, "diff_of", lambda _: None)

        assert mutation.report_command(10, 50.0) == 2
        assert mutation.report_command(10, 0.0) == 0


class TestMinScore:
    def test_should_default_to_the_ratchet(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MUTATION_MIN_SCORE", raising=False)

        assert mutation.min_score() == mutation.DEFAULT_MIN_SCORE

    def test_should_read_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MUTATION_MIN_SCORE", "72.5")

        assert mutation.min_score() == 72.5


class FakeProcess:
    def __init__(self, output: list[str], exit_code: int) -> None:
        self.stdout = iter(output)
        self._exit_code = exit_code

    def wait(self) -> int:
        return self._exit_code


class TestProcesses:
    def test_should_resolve_executables_to_an_absolute_path(self) -> None:
        assert Path(mutation.executable("python3")).is_absolute()

    def test_should_fail_when_an_executable_is_missing(self) -> None:
        with pytest.raises(FileNotFoundError, match="no-such-tool is not on the PATH"):
            mutation.executable("no-such-tool")

    def test_should_run_git_by_its_absolute_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []

        def run(command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
            calls.append(command)
            assert options == {"check": True, "capture_output": True, "text": True}
            return subprocess.CompletedProcess(command, 0, stdout="a.py\n")

        monkeypatch.setattr(mutation, "executable", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(mutation.subprocess, "run", run)
        assert mutation.git("diff", "--name-only") == "a.py\n"
        assert calls == [["/usr/bin/git", "diff", "--name-only"]]

    def test_should_stream_and_return_the_mutmut_output(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        commands: list[list[str]] = []

        def popen(command: list[str], **_: object) -> FakeProcess:
            commands.append(command)
            return FakeProcess(["1/2\n", "done\n"], 0)

        monkeypatch.setattr(mutation, "executable", lambda name: f"/venv/bin/{name}")
        monkeypatch.setattr(mutation.subprocess, "Popen", popen)
        assert mutation.run_mutmut(["a.*", "b.*"]) == (0, "1/2\ndone\n")
        assert commands == [["/venv/bin/mutmut", "run", "a.*", "b.*"]]
        assert capsys.readouterr().out == "1/2\ndone\n"


class TestSurvivorsSection:
    def test_should_show_the_diff_of_the_listed_survivors_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(mutation, "diff_of", lambda name: "-a\n+b" if name == "m1" else None)
        tally = mutation.Tally()
        for name in ("m1", "m2", "m3"):
            tally.add(name, mutation.Outcome.SURVIVED)
        assert mutation.survivors_section({"a.py": tally, "b.py": mutation.Tally()}, 2) == [
            "### Surviving mutants",
            "",
            "<details><summary><code>a.py</code>: 3</summary>",
            "",
            "`m1`",
            "```diff",
            "-a\n+b",
            "```",
            "`m2`",
            "... and 1 more (`mutmut results`)",
            "",
            "</details>",
            "",
        ]
