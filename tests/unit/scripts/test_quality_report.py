import json
import sys
from pathlib import Path

import pytest

from scripts import quality_report
from scripts.quality_report import (
    MARKER,
    SECTIONS,
    Analysis,
    DetailsFormat,
    Finding,
    Fragment,
    Status,
    analyze_bandit,
    analyze_eslint,
    analyze_frontend_build,
    analyze_import_linter,
    analyze_mutation,
    analyze_mypy,
    analyze_pip_audit,
    analyze_pytest,
    analyze_ruff_check,
    analyze_ruff_format,
    analyze_smoke,
    analyze_tsc,
    analyze_vitest,
    analyze_vulture,
    analyze_xenon,
    evaluate,
    load_fragments,
    parse_job_results,
    render,
)

PYTEST_OK = """tests/unit/test_a.py ....                                    [100%]

Name                 Stmts   Miss  Cover
----------------------------------------
app/a.py                10      0   100%
app/b.py                10      5    50%
app/c.py                10      2    80%
----------------------------------------
TOTAL                   30      7    77%
Coverage XML written to file coverage.xml
Required test coverage of 80.0% reached. Total coverage: 89.85%
============================== 34 passed in 4.18s ==============================
"""
PYTEST_LOW_COVERAGE = """Name    Stmts   Miss  Cover
app/b.py   10   5   50%
TOTAL      10      5    50%
FAIL Required test coverage of 80.0% not reached. Total coverage: 50.00%
============================== 34 passed in 4.18s ==============================
"""
PYTEST_FAILED = """FAILED tests/unit/test_a.py::test_should_x - assert 1 == 2
========================= 1 failed, 33 passed in 4.18s =========================
"""
PYTEST_NO_MINIMUM = """Name        Stmts   Miss  Cover
server.py      56      7    88%
TOTAL         530     27    95%
============================= 105 passed in 3.25s ==============================
"""
IMPORT_LINTER_OK = """---------
Contracts
---------

Analyzed 246 files, 968 dependencies.
-------------------------------------

Layers: main -> presentation -> infra -> domain KEPT
Infra does not import the web framework KEPT (1 ignored import)
Only factories wire infra: routes, dependencies, schemas, handlers and
middlewares do not KEPT (1 ignored import)

Contracts: 3 kept, 0 broken.
"""
IMPORT_LINTER_BROKEN = """Analyzed 246 files, 968 dependencies.
-------------------------------------

Layers: main -> presentation -> infra -> domain BROKEN
app.common is a leaf: it imports no other app layer KEPT

Contracts: 1 kept, 1 broken.


----------------
Broken contracts
----------------

Layers: main -> presentation -> infra -> domain
-----------------------------------------------

app.domain is not allowed to import app.infra:

- app.domain.usecases.health.check_readiness ->
app.infra.database.database_readiness_probe (l.18)
"""
SMOKE_OK = """
>> Starting a throwaway postgres:17-alpine (app-smoke-db-1)

>> alembic upgrade head (clean database)
   applied  -> 0001, initial schema
   applied 0001 -> 0002, second

>> alembic check (SQLAlchemy models vs migrations)
   ok  models match the migrations

>> Mode production-guard: ENV=production, AUTH_ENABLED=false must not start
   ok  refused to start

>> Mode auth-enabled: ENV=production, AUTH_ENABLED=true
   ok  API (auth-enabled) ready in 2.2s
   ok  GET    health                                                       200
   ok  GET    ready                                                        200
   ok  GET    workspaces                                                   401

>> Starting the MCP server (streamable-http) against http://127.0.0.1:1
   ok  MCP server ready in 1.4s
   ok  GET /health

>> MCP smoke passed

>> Mode database-down: liveness stays up, readiness reports the outage
   ok  API (database-down) ready in 3.1s
   ok  GET    health                                                       200
   ok  GET    ready                                                        503

>> Smoke passed
"""
SMOKE_FAILED = """
>> alembic upgrade head (clean database)
   applied  -> 0001, initial schema

>> alembic check (SQLAlchemy models vs migrations)
   WARNING: models and migrations drifted (set SMOKE_STRICT_SCHEMA=1 to fail):

>> Mode auth-enabled: ENV=production, AUTH_ENABLED=true
   ok  API (auth-enabled) ready in 2.2s
   ok  GET    health                                                       200

!! SMOKE FAILED: GET http://127.0.0.1:1/ready answered 503, expected 200. Body: {}

----- API log (/tmp/api.log) -----
Traceback: database is down
"""
ESLINT_WARNINGS = """
> frontend@0.1.0 lint
> eslint .

src/pages/Shared.tsx
  27:7  warning  Error: Calling setState synchronously within an effect

Effects are intended to synchronize state.

> 27 |       setState('not-found')
  30 |     let active = true  react-hooks/set-state-in-effect

src/shapes/Geo.tsx
  122:10  warning  Fast refresh only works when a file only exports components  react-refresh/only-export-components

✖ 2 problems (0 errors, 2 warnings)
"""
ESLINT_ERRORS = """src/a.ts
  1:1  error  'x' is defined but never used  @typescript-eslint/no-unused-vars

✖ 1 problem (1 error, 0 warnings)
"""
VITEST_OK = """ Test Files  19 passed (19)
      Tests  140 passed (140)
   Duration  54.38s

=============================== Coverage summary ===============================
Statements   : 21.34% ( 600/2811 )
Branches     : 21.04% ( 363/1725 )
Functions    : 16.73% ( 165/986 )
Lines        : 22.08% ( 564/2554 )
"""
BUILD_OK = """vite v6.4.3 building for production...
dist/index.html                                                0.51 kB │ gzip:   0.32 kB
dist/assets/index-CXlq8WX_.js                              3,019.03 kB │ gzip: 967.17 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
✓ built in 22.32s
"""


def fragment(
    analysis: Analysis, output: str, exit_code: int = 0, advisory: bool = False
) -> Fragment:
    return Fragment(analysis, exit_code, output, advisory)


def mutation_line(**overrides: object) -> str:
    data: dict[str, object] = {
        "skipped": False,
        "reason": "",
        "score": 75.0,
        "min_score": 60.0,
        "killed": 3,
        "total": 4,
        "targets": ["app.domain.usecases.a.*"],
        "files": [{"file": "app/domain/usecases/a.py", "total": 4, "killed": 3, "score": 75.0}],
        "survivors": [
            {
                "file": "app/domain/usecases/a.py",
                "function": "CreateA.execute",
                "status": "survived",
                "name": "app.domain.usecases.a.xǁCreateAǁexecute__mutmut_2",
                "diff": "-    if a > 0:\n+    if a > 1:",
            }
        ],
    }
    data.update(overrides)
    return "noise\nMUTATION_RESULT: " + json.dumps(data) + "\n"


class TestBackendAnalyzers:
    def test_should_count_ruff_lint_issues(self) -> None:
        finding = analyze_ruff_check(fragment(Analysis.RUFF_CHECK, "x\nFound 3 errors.", 1))

        assert finding.status == Status.FAILED
        assert finding.summary == "3 lint issues"

    def test_should_pass_ruff_lint_without_issues(self) -> None:
        assert (
            analyze_ruff_check(fragment(Analysis.RUFF_CHECK, "All checks passed!")).status
            == Status.OK
        )

    def test_should_count_files_to_reformat(self) -> None:
        output = "Would reformat: a.py\nWould reformat: b.py\n2 files would be reformatted"

        finding = analyze_ruff_format(fragment(Analysis.RUFF_FORMAT, output, 1))

        assert finding.summary.startswith("2 files need formatting")

    def test_should_summarise_mypy_success_and_errors(self) -> None:
        ok = analyze_mypy(fragment(Analysis.MYPY, "Success: no issues found in 247 source files"))
        failed = analyze_mypy(
            fragment(Analysis.MYPY, "a.py:1: error: x\nFound 1 error in 1 file", 1)
        )

        assert ok.summary == "No type errors (247 files)"
        assert (failed.status, failed.summary) == (Status.FAILED, "1 type error")

    def test_should_count_bandit_issues(self) -> None:
        output = ">> Issue: [B105] one\n>> Issue: [B106] two"

        assert analyze_bandit(fragment(Analysis.BANDIT, output, 1)).summary == "2 security issues"

    def test_should_count_pip_audit_vulnerabilities(self) -> None:
        output = "Found 1 known vulnerability in 1 package"

        assert (
            analyze_pip_audit(fragment(Analysis.PIP_AUDIT, output, 1)).summary == "1 vulnerability"
        )

    def test_should_report_advisory_dead_code_as_warning(self) -> None:
        output = "app/a.py:1: unused import 'x' (90% confidence)"

        finding = analyze_vulture(fragment(Analysis.VULTURE, output, 0, advisory=True))

        assert (finding.status, finding.summary) == (Status.WARNING, "1 dead code item")

    def test_should_pass_vulture_without_output(self) -> None:
        assert analyze_vulture(fragment(Analysis.VULTURE, "")).status == Status.OK

    def test_should_count_xenon_violations(self) -> None:
        output = "ERROR:xenon:block 'a.py:1 f' has a rank of C\nERROR:xenon:block 'b.py:2 g' has a rank of D"

        assert (
            analyze_xenon(fragment(Analysis.XENON, output, 1)).summary == "2 complexity violations"
        )


class TestPytestAnalyzer:
    def test_should_summarise_counts_and_coverage(self) -> None:
        finding = analyze_pytest(fragment(Analysis.PYTEST, PYTEST_OK))

        assert finding.status == Status.OK
        assert finding.summary == "34 passed, 0 failed · coverage 89.8% (minimum 80%)"

    def test_should_list_least_covered_files_first(self) -> None:
        details = analyze_pytest(fragment(Analysis.PYTEST, PYTEST_OK)).details

        lines = details.splitlines()
        assert lines[0].startswith("Name")
        assert lines[1].startswith("app/b.py")
        assert lines[2].startswith("app/c.py")
        assert "app/a.py" not in details
        assert lines[-1].startswith("TOTAL")

    def test_should_fail_when_coverage_is_below_the_minimum(self) -> None:
        finding = analyze_pytest(fragment(Analysis.PYTEST, PYTEST_LOW_COVERAGE, 1))

        assert finding.status == Status.FAILED
        assert "coverage below the minimum: 50.0% (minimum 80%)" in finding.summary

    def test_should_list_failed_tests(self) -> None:
        finding = analyze_pytest(fragment(Analysis.PYTEST, PYTEST_FAILED, 1))

        assert finding.summary.startswith("33 passed, 1 failed")
        assert "test_should_x" in finding.details

    def test_should_read_coverage_from_the_total_line_without_a_minimum(self) -> None:
        finding = analyze_pytest(fragment(Analysis.MCP_PYTEST, PYTEST_NO_MINIMUM))

        assert finding.summary == "105 passed, 0 failed · coverage 95.0%"

    def test_should_fail_when_pytest_crashes(self) -> None:
        finding = analyze_pytest(fragment(Analysis.PYTEST, "ImportError: boom", 4))

        assert finding.summary == "pytest failed before finishing"


class TestImportLinterAnalyzer:
    def test_should_parse_wrapped_contract_names_and_ignored_imports(self) -> None:
        finding = analyze_import_linter(fragment(Analysis.IMPORT_LINTER, IMPORT_LINTER_OK))

        assert finding.status == Status.OK
        assert finding.summary == "3 contracts kept (2 ignored imports in the baseline)"
        assert (
            "KEPT   Only factories wire infra: routes, dependencies, schemas, handlers and "
            "middlewares do not (1 ignored)"
        ) in finding.details

    def test_should_name_broken_contracts_and_show_the_violating_import(self) -> None:
        finding = analyze_import_linter(fragment(Analysis.IMPORT_LINTER, IMPORT_LINTER_BROKEN, 1))

        assert finding.status == Status.FAILED
        assert (
            finding.summary
            == "1 kept, 1 broken: **Layers: main -> presentation -> infra -> domain**"
        )
        assert "check_readiness ->" in finding.details
        assert finding.details.startswith("Broken contracts")

    def test_should_fail_when_no_contract_was_evaluated(self) -> None:
        finding = analyze_import_linter(fragment(Analysis.IMPORT_LINTER, "Invalid config", 1))

        assert finding.summary == "import-linter failed before evaluating the contracts"


class TestSmokeAnalyzer:
    def test_should_summarise_scenarios_probes_and_boot_time(self) -> None:
        finding = analyze_smoke(fragment(Analysis.SMOKE, SMOKE_OK))

        assert finding.status == Status.OK
        assert finding.summary == (
            "4/4 scenarios passed · /health ✅ · /ready ✅ · API ready in 3.1s · MCP ready in 1.4s"
        )
        assert finding.details_format == DetailsFormat.MARKDOWN
        assert "| `auth-enabled` | ✅ | 2.2s | 3 |  |" in finding.details
        assert (
            "| `migrations` | ✅ | - | 3 | 2 migrations applied on a clean database |"
            in finding.details
        )

    def test_should_show_the_failed_scenario_its_cause_and_the_logs(self) -> None:
        finding = analyze_smoke(fragment(Analysis.SMOKE, SMOKE_FAILED, 1))

        assert finding.status == Status.FAILED
        assert finding.summary.startswith("API started but failed: GET http://127.0.0.1:1/ready")
        assert "/ready ❌" in finding.summary
        assert "| `auth-enabled` | ❌ |" in finding.details
        assert "database is down" in finding.details

    def test_should_warn_when_models_and_migrations_drifted(self) -> None:
        output = SMOKE_OK.replace(
            "   ok  models match the migrations", "   WARNING: models and migrations drifted (x):"
        )

        finding = analyze_smoke(fragment(Analysis.SMOKE, output))

        assert finding.status == Status.WARNING
        assert finding.summary.endswith("⚠️ models and migrations drifted")

    def test_should_report_an_api_that_did_not_start(self) -> None:
        output = (
            ">> Mode auth-enabled: x\n!! SMOKE FAILED: API (auth-enabled) exited before answering\n"
        )

        finding = analyze_smoke(fragment(Analysis.SMOKE, output, 1))

        assert finding.summary.startswith("API did not start: API (auth-enabled) exited")


class TestMutationAnalyzer:
    def test_should_summarise_score_ratchet_and_survivors(self) -> None:
        finding = analyze_mutation(fragment(Analysis.MUTATION, mutation_line()))

        assert finding.status == Status.OK
        assert finding.summary == (
            "score 75.0% (ratchet 60%) · 3 of 4 mutants killed · 1 survivor in 1 changed file"
        )
        assert "| `app/domain/usecases/a.py` | `CreateA.execute` | survived |" in finding.details
        assert "```diff\n-    if a > 0:\n+    if a > 1:\n```" in finding.details

    def test_should_fail_below_the_ratchet(self) -> None:
        finding = analyze_mutation(fragment(Analysis.MUTATION, mutation_line(score=40.0), 1))

        assert finding.status == Status.FAILED

    def test_should_skip_when_nothing_changed(self) -> None:
        output = mutation_line(skipped=True, reason="No use case changed.", survivors=[], files=[])

        finding = analyze_mutation(fragment(Analysis.MUTATION, output))

        assert (finding.status, finding.summary) == (Status.SKIPPED, "No use case changed.")

    def test_should_fail_without_a_result_line(self) -> None:
        finding = analyze_mutation(fragment(Analysis.MUTATION, "Traceback: boom", 1))

        assert finding.summary == "mutmut failed before producing a score"


class TestFrontendAnalyzers:
    def test_should_warn_about_eslint_warnings_with_their_rules(self) -> None:
        finding = analyze_eslint(fragment(Analysis.ESLINT, ESLINT_WARNINGS))

        assert (finding.status, finding.summary) == (Status.WARNING, "0 errors, 2 warnings")
        assert "src/pages/Shared.tsx:27:7  warning  Error: Calling setState" in finding.details
        assert "[react-hooks/set-state-in-effect]" in finding.details
        assert "src/shapes/Geo.tsx:122:10" in finding.details
        assert "[react-refresh/only-export-components]" in finding.details

    def test_should_fail_on_eslint_errors(self) -> None:
        finding = analyze_eslint(fragment(Analysis.ESLINT, ESLINT_ERRORS, 1))

        assert (finding.status, finding.summary) == (Status.FAILED, "1 error, 0 warnings")

    def test_should_pass_eslint_without_problems(self) -> None:
        output = "> frontend@0.1.0 lint\n> eslint .\n"

        assert analyze_eslint(fragment(Analysis.ESLINT, output)).summary == "No lint problems"

    def test_should_count_tsc_errors(self) -> None:
        output = "src/a.ts(1,1): error TS2322: x\nsrc/b.ts(2,2): error TS2345: y"

        finding = analyze_tsc(fragment(Analysis.TSC, output, 2))

        assert (finding.status, finding.summary) == (Status.FAILED, "2 type errors")

    def test_should_pass_tsc(self) -> None:
        assert analyze_tsc(fragment(Analysis.TSC, "")).status == Status.OK

    def test_should_summarise_vitest_counts_and_coverage(self) -> None:
        finding = analyze_vitest(fragment(Analysis.VITEST, VITEST_OK))

        assert finding.status == Status.OK
        assert finding.summary == (
            "140 passed, 0 failed · coverage statements 21.34% / branches 21.04% / "
            "functions 16.73% / lines 22.08%"
        )

    def test_should_fail_on_vitest_failures(self) -> None:
        output = " FAIL  src/a.test.ts > does x\n      Tests  2 failed | 138 passed (140)\n"

        finding = analyze_vitest(fragment(Analysis.VITEST, output, 1))

        assert finding.status == Status.FAILED
        assert finding.summary.startswith("138 passed, 2 failed")
        assert "src/a.test.ts" in finding.details

    def test_should_fail_when_vitest_coverage_is_below_the_thresholds(self) -> None:
        output = VITEST_OK + "ERROR: Coverage for lines (5%) does not meet global threshold (10%)\n"

        finding = analyze_vitest(fragment(Analysis.VITEST, output, 1))

        assert finding.summary.endswith("coverage below the thresholds")
        assert finding.details.startswith("ERROR: Coverage for lines")

    def test_should_fail_when_vitest_crashes(self) -> None:
        finding = analyze_vitest(fragment(Analysis.VITEST, "SyntaxError", 1))

        assert finding.summary == "Vitest failed before finishing"

    def test_should_summarise_the_build(self) -> None:
        finding = analyze_frontend_build(fragment(Analysis.FRONTEND_BUILD, BUILD_OK))

        assert finding.status == Status.OK
        assert finding.summary == (
            "built in 22.32s · largest asset 3,019 kB · above Vite's chunk size warning"
        )

    def test_should_fail_the_build(self) -> None:
        output = "src/a.ts(1,1): error TS2322: x"

        finding = analyze_frontend_build(fragment(Analysis.FRONTEND_BUILD, output, 2))

        assert (finding.status, finding.details) == (Status.FAILED, output)


class TestMissingResults:
    @pytest.fixture
    def sut(self) -> quality_report.Section:
        return next(section for section in SECTIONS if section.title.startswith("Types"))

    @pytest.mark.parametrize(
        ("result", "status"),
        [
            ("cancelled", Status.SKIPPED),
            ("skipped", Status.SKIPPED),
            ("failure", Status.FAILED),
            ("success", Status.WARNING),
        ],
    )
    def test_should_explain_why_a_job_left_no_result(
        self, sut: quality_report.Section, result: str, status: Status
    ) -> None:
        fragments = {
            Analysis.MYPY: fragment(Analysis.MYPY, "Success: no issues found in 1 source file")
        }

        section = evaluate(sut, fragments, {"quality": "success", "mcp": result})

        assert section.status == status
        assert section.results[0].finding.status == Status.OK
        assert "`mcp`" in section.results[1].finding.summary

    def test_should_skip_jobs_that_did_not_run(self, sut: quality_report.Section) -> None:
        section = evaluate(sut, {}, {})

        assert section.status == Status.SKIPPED

    def test_should_not_break_when_an_analyzer_fails(
        self, sut: quality_report.Section, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def broken(_: Fragment) -> Finding:
            raise ValueError("unexpected output")

        monkeypatch.setitem(quality_report.ANALYZERS, Analysis.MYPY, broken)

        section = evaluate(
            sut, {Analysis.MYPY: fragment(Analysis.MYPY, "?", 1)}, {"mcp": "success"}
        )

        assert section.results[0].finding.status == Status.FAILED
        assert "could not be summarised" in section.results[0].finding.summary


class TestRender:
    @pytest.fixture
    def sut(self) -> dict[Analysis, Fragment]:
        return {
            Analysis.RUFF_CHECK: fragment(Analysis.RUFF_CHECK, "All checks passed!"),
            Analysis.RUFF_FORMAT: fragment(Analysis.RUFF_FORMAT, "3 files already formatted"),
            Analysis.PYTEST: fragment(Analysis.PYTEST, PYTEST_FAILED, 1),
            Analysis.SMOKE: fragment(Analysis.SMOKE, SMOKE_OK),
        }

    def test_should_start_with_the_marker_verdict_and_one_row_per_section(
        self, sut: dict[Analysis, Fragment]
    ) -> None:
        report = render(sut, {"quality": "failure", "mcp": "success"}, "commit `abc1234`")

        lines = report.splitlines()
        assert lines[0] == MARKER
        assert lines[1] == "## 🔍 Quality Report"
        assert lines[3].startswith("❌ **Failed**")
        rows = [line for line in lines if line.startswith(("| Backend |", "| Frontend |"))]
        assert len(rows) == len(SECTIONS)
        assert "| Backend | Lint and format (ruff) | ✅ | lint: ✅ · format: ✅ |" in rows
        assert report.rstrip().endswith("commit `abc1234`")

    def test_should_render_markdown_details_unfenced_and_text_details_fenced(
        self, sut: dict[Analysis, Fragment]
    ) -> None:
        report = render(sut, {})

        assert "<details><summary>Scenarios</summary>\n\n| Scenario |" in report
        assert "<details><summary>Failures</summary>\n\n```text\nFAILED tests" in report

    def test_should_say_all_good_when_nothing_failed(self) -> None:
        fragments = {
            Analysis.RUFF_CHECK: fragment(Analysis.RUFF_CHECK, "All checks passed!"),
            Analysis.RUFF_FORMAT: fragment(Analysis.RUFF_FORMAT, "3 files already formatted"),
        }

        report = render(fragments, {})

        assert "✅ **All good** (12 sections not run)" in report

    def test_should_trim_details_to_fit_in_a_comment(self) -> None:
        huge = "E" * 5000 + "\n"
        fragments = (
            {
                analysis: fragment(analysis, huge * 3, 1)
                for analysis in (
                    Analysis.RUFF_CHECK,
                    Analysis.MYPY,
                    Analysis.BANDIT,
                    Analysis.XENON,
                )
            }
            | {
                analysis: fragment(analysis, huge * 3, 1)
                for analysis in (
                    Analysis.PIP_AUDIT,
                    Analysis.TSC,
                    Analysis.MCP_MYPY,
                    Analysis.ESLINT,
                )
            }
            | {
                analysis: fragment(analysis, huge * 3, 1)
                for analysis in (
                    Analysis.RUFF_FORMAT,
                    Analysis.PYTEST,
                    Analysis.MCP_PYTEST,
                    Analysis.VITEST,
                )
            }
        )

        report = render(fragments, {})

        assert len(report) <= quality_report.MAX_REPORT_CHARS
        assert "Details were trimmed" in report


class TestFragments:
    def test_should_round_trip_a_fragment(self, tmp_path: Path) -> None:
        sut = Fragment(Analysis.MYPY, 1, "out", advisory=True, seconds=1.5)

        path = sut.write(tmp_path)

        assert Fragment.read(path) == sut

    def test_should_ignore_invalid_fragments(self, tmp_path: Path) -> None:
        Fragment(Analysis.TSC, 0, "").write(tmp_path)
        (tmp_path / "broken.json").write_text("{not json")
        (tmp_path / "unknown.json").write_text(json.dumps({"analysis": "nope", "exit_code": 0}))

        assert list(load_fragments(tmp_path)) == [Analysis.TSC]

    def test_should_read_job_results_from_needs(self) -> None:
        needs = json.dumps({"lint": {"result": "success", "outputs": {}}, "smoke": {}})

        assert parse_job_results(needs) == {"lint": "success", "smoke": "unknown"}
        assert parse_job_results("") == {}


class TestCommandLine:
    def test_should_store_the_output_and_keep_the_exit_code(self, tmp_path: Path) -> None:
        command = [sys.executable, "-c", "import sys; print('boom'); sys.exit(3)"]

        exit_code = quality_report.run_command(Analysis.XENON, command, tmp_path, advisory=False)

        stored = Fragment.read(tmp_path / "xenon.json")
        assert exit_code == 3
        assert (stored.exit_code, stored.output) == (3, "boom\n")

    def test_should_not_fail_an_advisory_analysis(self, tmp_path: Path) -> None:
        command = [sys.executable, "-c", "import sys; sys.exit(1)"]

        assert quality_report.run_command(Analysis.VULTURE, command, tmp_path, advisory=True) == 0
        assert Fragment.read(tmp_path / "vulture.json").advisory is True

    def test_should_strip_the_working_directory_from_the_output(self, tmp_path: Path) -> None:
        command = [sys.executable, "-c", "import os; print(os.getcwd() + '/src/a.ts')"]

        quality_report.run_command(Analysis.TSC, command, tmp_path, advisory=False)

        assert Fragment.read(tmp_path / "tsc.json").output == "src/a.ts\n"

    def test_should_record_a_missing_tool(self, tmp_path: Path) -> None:
        exit_code = quality_report.run_command(
            Analysis.TSC, ["definitely-not-a-command-xyz"], tmp_path, advisory=False
        )

        assert exit_code == 127
        assert "could not run" in Fragment.read(tmp_path / "tsc.json").output

    def test_should_require_a_command_after_the_separator(self) -> None:
        assert quality_report.main(["run", "mypy"]) == 2

    def test_should_run_and_render_from_the_command_line(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_RUN_ID", "42")
        monkeypatch.setenv("QUALITY_REPORT_SHA", "abcdef1234")
        fragments = tmp_path / "fragments"
        output = tmp_path / "report.md"
        quality_report.main(["run", "tsc", "--dir", str(fragments), "--", sys.executable, "-c", ""])

        exit_code = quality_report.main(
            ["render", "--dir", str(fragments), "--needs-json", "{}", "--output", str(output)]
        )

        report = output.read_text()
        assert exit_code == 0
        assert "| Frontend | Types (tsc) | ✅ | No type errors |" in report
        assert (
            "commit `abcdef1` · [CI run](https://github.com/owner/repo/actions/runs/42)" in report
        )

    def test_should_have_no_footer_outside_github_actions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
        monkeypatch.delenv("GITHUB_RUN_ID", raising=False)

        assert quality_report.footer_from_environment() == ""
