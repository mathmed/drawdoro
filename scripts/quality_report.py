import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger(__name__)

MARKER = "<!-- quality-report -->"
DEFAULT_DIRECTORY = Path("quality-fragments")
MAX_DETAILS_CHARS = 6000
# GitHub rejects comments above 65536 characters; the report is re-rendered with less detail.
MAX_REPORT_CHARS = 60000
REDUCED_DETAILS_CHARS = (1500, 0)
MAX_SURVIVORS_LISTED = 30
MAX_COVERAGE_ROWS = 10
# Must match scripts/mutation.py, which prints this line followed by a JSON document
MUTATION_RESULT_PREFIX = "MUTATION_RESULT: "
UV_NOISE = re.compile(r"^warning: `VIRTUAL_ENV=.*$", re.MULTILINE)
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class Analysis(StrEnum):
    RUFF_CHECK = "ruff-check"
    RUFF_FORMAT = "ruff-format"
    MYPY = "mypy"
    MCP_MYPY = "mcp-mypy"
    BANDIT = "bandit"
    PIP_AUDIT = "pip-audit"
    VULTURE = "vulture"
    XENON = "xenon"
    PYTEST = "pytest"
    MCP_PYTEST = "mcp-pytest"
    IMPORT_LINTER = "import-linter"
    MCP_IMPORT_LINTER = "mcp-import-linter"
    SMOKE = "smoke"
    MUTATION = "mutation"
    ESLINT = "eslint"
    TSC = "tsc"
    VITEST = "vitest"
    FRONTEND_BUILD = "frontend-build"


class Status(StrEnum):
    OK = "✅"
    WARNING = "⚠️"
    FAILED = "❌"
    SKIPPED = "⏭️"


class Area(StrEnum):
    BACKEND = "Backend"
    FRONTEND = "Frontend"


class DetailsFormat(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"


SEVERITY_ORDER = [Status.OK, Status.SKIPPED, Status.WARNING, Status.FAILED]


def worst(statuses: list[Status]) -> Status:
    return max(statuses, key=SEVERITY_ORDER.index, default=Status.OK)


@dataclass(frozen=True)
class Fragment:
    analysis: Analysis
    exit_code: int
    output: str
    advisory: bool = False
    seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def write(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.analysis}.json"
        payload = {
            "analysis": self.analysis.value,
            "exit_code": self.exit_code,
            "output": self.output,
            "advisory": self.advisory,
            "seconds": self.seconds,
        }
        path.write_text(json.dumps(payload))
        return path

    @classmethod
    def read(cls, path: Path) -> Fragment:
        data = json.loads(path.read_text())
        return cls(
            analysis=Analysis(data["analysis"]),
            exit_code=int(data["exit_code"]),
            output=str(data["output"]),
            advisory=bool(data.get("advisory", False)),
            seconds=float(data.get("seconds", 0.0)),
        )


@dataclass(frozen=True)
class Finding:
    status: Status
    summary: str
    details: str = ""
    details_title: str = "Output"
    details_format: DetailsFormat = DetailsFormat.TEXT


@dataclass(frozen=True)
class Check:
    analysis: Analysis
    job: str
    label: str = ""


@dataclass(frozen=True)
class Section:
    area: Area
    title: str
    checks: tuple[Check, ...]


# One entry per section of the report. `job` is the CI job that uploads the fragment
# (quality-fragment-<job>); it must also be listed in the `needs` of the quality-report job.
SECTIONS = [
    Section(
        Area.BACKEND,
        "Lint and format (ruff)",
        (Check(Analysis.RUFF_CHECK, "lint", "lint"), Check(Analysis.RUFF_FORMAT, "lint", "format")),
    ),
    Section(
        Area.BACKEND,
        "Types (mypy)",
        (Check(Analysis.MYPY, "quality", "app"), Check(Analysis.MCP_MYPY, "mcp", "mcp")),
    ),
    Section(
        Area.BACKEND,
        "Security (bandit, pip-audit)",
        (
            Check(Analysis.BANDIT, "quality", "bandit"),
            Check(Analysis.PIP_AUDIT, "quality", "pip-audit"),
        ),
    ),
    Section(Area.BACKEND, "Dead code (vulture)", (Check(Analysis.VULTURE, "quality"),)),
    Section(Area.BACKEND, "Complexity (xenon)", (Check(Analysis.XENON, "quality"),)),
    Section(
        Area.BACKEND,
        "Tests and coverage (pytest)",
        (Check(Analysis.PYTEST, "quality", "app"), Check(Analysis.MCP_PYTEST, "mcp", "mcp")),
    ),
    Section(
        Area.BACKEND,
        "Architecture (import-linter)",
        (
            Check(Analysis.IMPORT_LINTER, "lint", "app"),
            Check(Analysis.MCP_IMPORT_LINTER, "mcp", "mcp"),
        ),
    ),
    Section(Area.BACKEND, "Boot smoke (API and MCP)", (Check(Analysis.SMOKE, "smoke"),)),
    Section(Area.BACKEND, "Mutation testing (mutmut)", (Check(Analysis.MUTATION, "mutation"),)),
    Section(Area.FRONTEND, "Lint (ESLint)", (Check(Analysis.ESLINT, "frontend"),)),
    Section(Area.FRONTEND, "Types (tsc)", (Check(Analysis.TSC, "frontend"),)),
    Section(Area.FRONTEND, "Tests and coverage (Vitest)", (Check(Analysis.VITEST, "frontend"),)),
    Section(Area.FRONTEND, "Build (Vite)", (Check(Analysis.FRONTEND_BUILD, "frontend"),)),
]


@dataclass(frozen=True)
class CheckResult:
    check: Check
    finding: Finding
    seconds: float = 0.0


@dataclass(frozen=True)
class SectionResult:
    section: Section
    status: Status
    results: list[CheckResult]


def clean(output: str) -> str:
    return ANSI_ESCAPE.sub("", UV_NOISE.sub("", output)).strip()


def tail(text: str, limit: int = MAX_DETAILS_CHARS) -> str:
    if len(text) <= limit:
        return text
    return "[...truncated...]\n" + text[-limit:]


def first_int(pattern: str, text: str, default: int = 0) -> int:
    match = re.search(pattern, text)
    return int(match[1].replace(",", "")) if match else default


def plural(count: int, singular: str, plural_form: str) -> str:
    return f"{count} {singular if count == 1 else plural_form}"


def matching_lines(pattern: str, text: str) -> str:
    return "\n".join(line for line in text.splitlines() if re.search(pattern, line))


def analyze_ruff_check(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        return Finding(Status.OK, "No lint issues")
    count = first_int(r"Found (\d+) error", output)
    summary = plural(count, "lint issue", "lint issues") if count else "Lint failed"
    return Finding(Status.FAILED, summary, tail(output))


def analyze_ruff_format(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        return Finding(Status.OK, "Formatting is correct")
    count = len(re.findall(r"^Would reformat: ", output, re.MULTILINE))
    summary = (
        f"{plural(count, 'file', 'files')} need formatting (`make format-code`)"
        if count
        else "Format check failed"
    )
    return Finding(Status.FAILED, summary, tail(output))


def analyze_mypy(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        files = first_int(r"no issues found in (\d+) source file", output)
        return Finding(Status.OK, f"No type errors ({plural(files, 'file', 'files')})")
    errors = first_int(r"Found (\d+) error", output)
    summary = plural(errors, "type error", "type errors") if errors else "mypy failed"
    return Finding(Status.FAILED, summary, tail(output))


def analyze_bandit(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        return Finding(Status.OK, "No medium or high severity issues")
    issues = len(re.findall(r">> Issue:", output))
    summary = plural(issues, "security issue", "security issues") if issues else "bandit failed"
    return Finding(Status.FAILED, summary, tail(output))


def analyze_pip_audit(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        return Finding(Status.OK, "No known vulnerabilities")
    count = first_int(r"Found (\d+) known vulnerabilit", output)
    summary = plural(count, "vulnerability", "vulnerabilities") if count else "pip-audit failed"
    return Finding(Status.FAILED, summary, tail(output))


def analyze_vulture(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed and not output:
        return Finding(Status.OK, "No dead code detected")
    lines = [line for line in output.splitlines() if line.strip()]
    status = Status.WARNING if fragment.advisory else Status.FAILED
    return Finding(status, plural(len(lines), "dead code item", "dead code items"), tail(output))


def analyze_xenon(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        return Finding(Status.OK, "Complexity within the thresholds")
    blocks = len(re.findall(r"^ERROR:xenon:", output, re.MULTILINE))
    summary = (
        plural(blocks, "complexity violation", "complexity violations")
        if blocks
        else "Complexity above the thresholds"
    )
    return Finding(Status.FAILED, summary, tail(output))


COVERAGE_ROW = re.compile(r"^(?P<name>\S+)\s+\d+\s+\d+\s+(?:\d+\s+\d+\s+)?(?P<cover>\d+)%")


def least_covered(output: str) -> str:
    lines = output.splitlines()
    header = next((line for line in lines if line.startswith("Name ")), None)
    total = next((line for line in lines if line.startswith("TOTAL")), None)
    if header is None or total is None:
        return ""
    rows = [
        (int(match["cover"]), line)
        for line in lines
        if (match := COVERAGE_ROW.match(line)) and not line.startswith("TOTAL")
    ]
    lowest = [line for cover, line in sorted(rows, key=lambda row: row[0]) if cover < 100]
    listed = lowest[:MAX_COVERAGE_ROWS]
    hidden = len(lowest) - len(listed)
    footer = [f"... and {hidden} more files below 100%"] if hidden > 0 else []
    return "\n".join([header, *listed, *footer, total])


def coverage_of(output: str) -> str:
    total = re.search(r"Total coverage: ([\d.]+)%", output)
    if total is None:
        total = re.search(r"^TOTAL\s.*?(\d+(?:\.\d+)?)%\s*$", output, re.MULTILINE)
    required = re.search(r"Required test coverage of ([\d.]+)%", output)
    text = f"{float(total[1]):.1f}%" if total else "n/a"
    return text + (f" (minimum {float(required[1]):.0f}%)" if required else "")


def analyze_pytest(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    summary_line = next(
        (
            line
            for line in reversed(output.splitlines())
            if re.search(r" in [\d.]+s", line) and re.search(r"\d+ (passed|failed|error)", line)
        ),
        "",
    )
    passed = first_int(r"(\d+) passed", summary_line)
    failed = first_int(r"(\d+) failed", summary_line) + first_int(r"(\d+) errors?", summary_line)
    skipped = first_int(r"(\d+) skipped", summary_line)
    counts = f"{passed} passed, {failed} failed" + (f", {skipped} skipped" if skipped else "")
    coverage = coverage_of(output)
    if not summary_line:
        return Finding(Status.FAILED, "pytest failed before finishing", tail(output))
    if failed:
        failures = matching_lines(r"^(FAILED|ERROR) ", output) or output
        return Finding(Status.FAILED, f"{counts} · coverage {coverage}", tail(failures), "Failures")
    table = least_covered(output)
    status = Status.OK if fragment.passed else Status.FAILED
    prefix = "coverage below the minimum: " if not fragment.passed else "coverage "
    return Finding(status, f"{counts} · {prefix}{coverage}", table, "Least covered files")


CONTRACTS_BLOCK = re.compile(r"dependencies\.\n-+\n(?P<body>.*?)\n\s*Contracts: ", re.DOTALL)
CONTRACT_ENTRY = re.compile(
    r"(?P<name>\S.*?) (?P<state>KEPT|BROKEN)(?: \((?P<ignored>\d+) ignored imports?\))?(?=\s|$)"
)


def parse_contracts(output: str) -> list[tuple[str, str, int]]:
    block = CONTRACTS_BLOCK.search(output)
    if block is None:
        return []
    # import-linter wraps long contract names over several lines.
    flat = " ".join(line.strip() for line in block["body"].splitlines() if line.strip())
    return [
        (match["name"], match["state"], int(match["ignored"] or 0))
        for match in CONTRACT_ENTRY.finditer(flat)
    ]


def analyze_import_linter(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    contracts = parse_contracts(output)
    if not contracts:
        return Finding(
            Status.FAILED, "import-linter failed before evaluating the contracts", tail(output)
        )
    kept = sum(state == "KEPT" for _, state, _ in contracts)
    ignored = sum(count for _, _, count in contracts)
    baseline = f" ({plural(ignored, 'ignored import', 'ignored imports')} in the baseline)"
    listing = "\n".join(
        f"{state:6} {name}" + (f" ({count} ignored)" if count else "")
        for name, state, count in contracts
    )
    broken = [name for name, state, _ in contracts if state == "BROKEN"]
    if not broken and fragment.passed:
        summary = plural(kept, "contract kept", "contracts kept") + (baseline if ignored else "")
        return Finding(Status.OK, summary, listing, "Contracts")
    marker = output.find("Broken contracts")
    violation = output[marker:] if marker >= 0 else output
    summary = f"{kept} kept, {len(broken)} broken: " + "; ".join(f"**{name}**" for name in broken)
    return Finding(
        Status.FAILED, summary, tail(violation), "Broken contracts and violating imports"
    )


FRAGMENT_HEADER = re.compile(
    r"^>> (?:Mode (?P<mode>[\w-]+): .*|(?P<mcp>Starting the MCP server).*|(?P<db>alembic upgrade head).*)$",
    re.MULTILINE,
)
FAILURE_LINE = re.compile(r"^!! (?:MCP )?SMOKE FAILED: (?P<reason>.+)$", re.MULTILINE)
READY_LINE = re.compile(r"^\s+ok\s+(?P<name>.+?) ready in (?P<seconds>[\d.]+)s$", re.MULTILINE)
OK_LINE = re.compile(r"^\s+ok\s+", re.MULTILINE)
APPLIED_LINE = re.compile(r"^\s+applied\s", re.MULTILINE)
DRIFT_WARNING = "WARNING: models and migrations drifted"


@dataclass(frozen=True)
class SmokeStep:
    name: str
    status: Status
    ready_seconds: str
    checks: int
    note: str = ""


def smoke_step(name: str, text: str, finished: bool) -> SmokeStep:
    ready = READY_LINE.search(text)
    seconds = f"{ready['seconds']}s" if ready else "-"
    checks = len(OK_LINE.findall(text)) - (1 if ready else 0)
    applied = len(APPLIED_LINE.findall(text))
    checks += applied
    failure = FAILURE_LINE.search(text)
    if failure:
        return SmokeStep(name, Status.FAILED, seconds, checks, failure["reason"])
    if not finished:
        return SmokeStep(name, Status.FAILED, seconds, checks, "stopped without finishing")
    note = (
        f"{plural(applied, 'migration', 'migrations')} applied on a clean database"
        if applied
        else ""
    )
    if DRIFT_WARNING in text:
        drift = "; ".join(part for part in (note, "models and migrations drifted") if part)
        return SmokeStep(name, Status.WARNING, seconds, checks, drift)
    return SmokeStep(name, Status.OK, seconds, checks, note)


def smoke_steps(output: str) -> list[SmokeStep]:
    headers = list(FRAGMENT_HEADER.finditer(output))
    passed = ">> Smoke passed" in output
    steps: list[SmokeStep] = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(output)
        text = output[header.start() : end]
        name = header["mode"] or ("mcp" if header["mcp"] else "migrations")
        if header["mcp"]:
            finished = ">> MCP smoke passed" in text
        else:
            finished = index + 1 < len(headers) or passed
        steps.append(smoke_step(name, text, finished))
    return steps


def smoke_table(steps: list[SmokeStep]) -> str:
    rows = [
        f"| `{step.name}` | {step.status} | {step.ready_seconds} | {step.checks} | {step.note} |"
        for step in steps
    ]
    return "\n".join(
        ["| Scenario | Result | Ready in | Checks | Note |", "|---|---|---|---|---|", *rows]
    )


def probe_status(output: str, path: str) -> str:
    return "✅" if re.search(rf"^\s+ok\s+GET\s+{path}\s+200$", output, re.MULTILINE) else "❌"


def analyze_smoke(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    steps = smoke_steps(output)
    ready = [(m["name"], float(m["seconds"])) for m in READY_LINE.finditer(output)]
    api = [seconds for name, seconds in ready if name.startswith("API")]
    mcp = [seconds for name, seconds in ready if name.startswith("MCP")]
    boot = " · ".join(
        f"{name} ready in {max(times):.1f}s"
        for name, times in (("API", api), ("MCP", mcp))
        if times
    )
    probes = f"/health {probe_status(output, 'health')} · /ready {probe_status(output, 'ready')}"
    scenarios = [step for step in steps if step.name != "migrations"]
    ok = sum(step.status != Status.FAILED for step in scenarios)
    counts = f"{ok}/{len(scenarios)} scenarios passed"
    table = smoke_table(steps)
    if fragment.passed:
        status = worst([step.status for step in steps])
        drift = " · ⚠️ models and migrations drifted" if status == Status.WARNING else ""
        summary = " · ".join(part for part in (counts, probes, boot) if part) + drift
        return Finding(status, summary, table, "Scenarios", DetailsFormat.MARKDOWN)
    failure = FAILURE_LINE.search(output)
    cause = f": {failure['reason']}" if failure else ""
    started = "started but failed" if ready else "did not start"
    logs = output[failure.start() :] if failure else output
    details = f"{table}\n\n" + fence(tail(logs, MAX_DETAILS_CHARS // 2))
    return Finding(
        Status.FAILED,
        f"API {started}{cause} · {counts} · {probes}",
        details,
        "Scenarios and logs",
        DetailsFormat.MARKDOWN,
    )


@dataclass(frozen=True)
class Survivor:
    file: str
    function: str
    status: str
    name: str
    diff: str = ""


@dataclass(frozen=True)
class FileScore:
    file: str
    total: int
    killed: int
    score: float


@dataclass(frozen=True)
class MutationOutcome:
    skipped: bool
    reason: str
    score: float
    min_score: float
    killed: int
    total: int
    files: list[FileScore]
    survivors: list[Survivor]

    @classmethod
    def parse(cls, output: str) -> MutationOutcome | None:
        line = next(
            (line for line in output.splitlines() if line.startswith(MUTATION_RESULT_PREFIX)), None
        )
        if line is None:
            return None
        data = json.loads(line.removeprefix(MUTATION_RESULT_PREFIX))
        return cls(
            skipped=bool(data["skipped"]),
            reason=str(data.get("reason", "")),
            score=float(data["score"]),
            min_score=float(data["min_score"]),
            killed=int(data["killed"]),
            total=int(data["total"]),
            files=[FileScore(**item) for item in data.get("files", [])],
            survivors=[Survivor(**item) for item in data["survivors"]],
        )


def mutation_details(outcome: MutationOutcome) -> str:
    lines = ["| File | Mutants | Killed | Score |", "|---|---:|---:|---:|"]
    lines += [f"| `{f.file}` | {f.total} | {f.killed} | {f.score:.1f}% |" for f in outcome.files]
    if not outcome.survivors:
        return "\n".join(lines)
    listed = outcome.survivors[:MAX_SURVIVORS_LISTED]
    lines += ["", "**Survivors in the changed code**", "", "| File | Function | Status |"]
    lines += ["|---|---|---|"]
    lines += [f"| `{s.file}` | `{s.function}` | {s.status} |" for s in listed]
    hidden = len(outcome.survivors) - len(listed)
    if hidden > 0:
        lines.append(f"\n... and {hidden} more: see the `mutation` job summary.")
    diffs = [s for s in listed if s.diff]
    for survivor in diffs:
        lines += ["", f"`{survivor.name}`", "```diff", survivor.diff.replace("```", "'''"), "```"]
    lines += [
        "",
        "Reproduce locally with `make mutation-changed`, then `uv run mutmut show <name>`.",
    ]
    return "\n".join(lines)


def analyze_mutation(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    outcome = MutationOutcome.parse(output)
    if outcome is None:
        return Finding(Status.FAILED, "mutmut failed before producing a score", tail(output))
    if outcome.skipped:
        return Finding(Status.SKIPPED, outcome.reason or "Nothing to mutate")
    survivors = len(outcome.survivors)
    summary = (
        f"score {outcome.score:.1f}% (ratchet {outcome.min_score:.0f}%) · "
        f"{outcome.killed} of {outcome.total} mutants killed · "
        f"{plural(survivors, 'survivor', 'survivors')} in "
        f"{plural(len(outcome.files), 'changed file', 'changed files')}"
    )
    status = Status.OK if outcome.score >= outcome.min_score else Status.FAILED
    return Finding(
        status,
        summary,
        mutation_details(outcome),
        "Changed files and survivors",
        DetailsFormat.MARKDOWN,
    )


ESLINT_PROBLEMS = re.compile(r"(\d+) problems? \((\d+) errors?, (\d+) warnings?\)")
ESLINT_ISSUE = re.compile(r"^\s+\d+:\d+\s+(?:warning|error)\s+")
ESLINT_FILE = re.compile(r"^\S+\.(?:[cm]?[jt]sx?)$")
ESLINT_RULE = re.compile(r"\s(?P<rule>[\w@-]+/[\w-]+)$")
ESLINT_RULE_LOOKAHEAD = 20


def eslint_rule(lines: list[str], index: int) -> str:
    for line in lines[index : index + ESLINT_RULE_LOOKAHEAD]:
        match = ESLINT_RULE.search(line)
        if match:
            return match["rule"]
    return ""


def eslint_issues(output: str) -> str:
    lines = output.splitlines()
    current_file = ""
    issues: list[str] = []
    for index, line in enumerate(lines):
        if ESLINT_FILE.match(line):
            current_file = line
        if not ESLINT_ISSUE.match(line):
            continue
        message = re.sub(r"\s{2,}\S+/[\w-]+$", "", line.strip())[:160]
        rule = eslint_rule(lines, index)
        issues.append(f"{current_file}:{message}" + (f" [{rule}]" if rule else ""))
    return "\n".join(issues)


def analyze_eslint(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    problems = ESLINT_PROBLEMS.search(output)
    errors = int(problems[2]) if problems else 0
    warnings = int(problems[3]) if problems else 0
    counts = f"{plural(errors, 'error', 'errors')}, {plural(warnings, 'warning', 'warnings')}"
    if fragment.passed and not warnings:
        return Finding(Status.OK, "No lint problems")
    details = tail(eslint_issues(output) or output)
    if fragment.passed:
        return Finding(Status.WARNING, counts, details, "Problems")
    return Finding(Status.FAILED, counts if problems else "ESLint failed", details, "Problems")


def analyze_tsc(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if fragment.passed:
        return Finding(Status.OK, "No type errors")
    errors = matching_lines(r"error TS\d+", output)
    count = len(errors.splitlines()) if errors else 0
    summary = plural(count, "type error", "type errors") if count else "tsc failed"
    return Finding(Status.FAILED, summary, tail(errors or output))


VITEST_COVERAGE = re.compile(
    r"^(Statements|Branches|Functions|Lines)\s*:\s*([\d.]+)%", re.MULTILINE
)


def vitest_counts(output: str) -> tuple[int, int] | None:
    line = re.search(r"^\s*Tests\s+(.+)$", output, re.MULTILINE)
    if line is None:
        return None
    return first_int(r"(\d+) passed", line[1]), first_int(r"(\d+) failed", line[1])


def analyze_vitest(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    counts = vitest_counts(output)
    coverage = {name.lower(): value for name, value in VITEST_COVERAGE.findall(output)}
    coverage_text = (
        " / ".join(f"{name} {value}%" for name, value in coverage.items()) if coverage else "n/a"
    )
    if counts is None:
        return Finding(Status.FAILED, "Vitest failed before finishing", tail(output))
    passed, failed = counts
    summary = f"{passed} passed, {failed} failed · coverage {coverage_text}"
    if failed:
        failures = matching_lines(r"(FAIL|×|✗) ", output) or output
        return Finding(Status.FAILED, summary, tail(failures), "Failures")
    thresholds = matching_lines(r"^ERROR: Coverage for ", output)
    if not fragment.passed:
        detail = thresholds or tail(output)
        reason = "coverage below the thresholds" if thresholds else "Vitest failed"
        return Finding(Status.FAILED, f"{summary} · {reason}", detail, "Output")
    return Finding(Status.OK, summary)


BUILD_ASSET = re.compile(r"^dist/\S+\s+(?P<size>[\d,.]+) kB", re.MULTILINE)


def analyze_frontend_build(fragment: Fragment) -> Finding:
    output = clean(fragment.output)
    if not fragment.passed:
        errors = matching_lines(r"error", output)
        return Finding(Status.FAILED, "Build failed", tail(errors or output))
    built = re.search(r"built in ([\d.]+m?s)", output)
    sizes = [float(match["size"].replace(",", "")) for match in BUILD_ASSET.finditer(output)]
    parts = [f"built in {built[1]}" if built else "built"]
    if sizes:
        parts.append(f"largest asset {max(sizes):,.0f} kB")
    if "Some chunks are larger than" in output:
        parts.append("above Vite's chunk size warning")
    return Finding(Status.OK, " · ".join(parts))


ANALYZERS: dict[Analysis, Callable[[Fragment], Finding]] = {
    Analysis.RUFF_CHECK: analyze_ruff_check,
    Analysis.RUFF_FORMAT: analyze_ruff_format,
    Analysis.MYPY: analyze_mypy,
    Analysis.MCP_MYPY: analyze_mypy,
    Analysis.BANDIT: analyze_bandit,
    Analysis.PIP_AUDIT: analyze_pip_audit,
    Analysis.VULTURE: analyze_vulture,
    Analysis.XENON: analyze_xenon,
    Analysis.PYTEST: analyze_pytest,
    Analysis.MCP_PYTEST: analyze_pytest,
    Analysis.IMPORT_LINTER: analyze_import_linter,
    Analysis.MCP_IMPORT_LINTER: analyze_import_linter,
    Analysis.SMOKE: analyze_smoke,
    Analysis.MUTATION: analyze_mutation,
    Analysis.ESLINT: analyze_eslint,
    Analysis.TSC: analyze_tsc,
    Analysis.VITEST: analyze_vitest,
    Analysis.FRONTEND_BUILD: analyze_frontend_build,
}


def missing_finding(job: str, job_results: dict[str, str]) -> Finding:
    result = job_results.get(job)
    if result is None:
        return Finding(Status.SKIPPED, f"Job `{job}` did not run: analysis not run")
    if result in ("cancelled", "skipped"):
        return Finding(Status.SKIPPED, f"Job `{job}` was {result}: analysis not run")
    if result == "success":
        return Finding(Status.WARNING, f"Job `{job}` passed but its result was not uploaded")
    return Finding(Status.FAILED, f"Job `{job}` ended as `{result}` before running this analysis")


def analyze(fragment: Fragment) -> Finding:
    try:
        return ANALYZERS[fragment.analysis](fragment)
    except (ValueError, KeyError, TypeError, IndexError) as error:
        logger.warning("could not analyse %s: %s", fragment.analysis, error)
        status = Status.OK if fragment.passed else Status.FAILED
        verdict = "passed" if fragment.passed else f"failed (exit code {fragment.exit_code})"
        return Finding(
            status, f"{verdict}; the output could not be summarised", tail(clean(fragment.output))
        )


def evaluate(
    section: Section, fragments: dict[Analysis, Fragment], job_results: dict[str, str]
) -> SectionResult:
    results: list[CheckResult] = []
    for check in section.checks:
        fragment = fragments.get(check.analysis)
        if fragment is None:
            results.append(CheckResult(check, missing_finding(check.job, job_results)))
            continue
        results.append(CheckResult(check, analyze(fragment), fragment.seconds))
    return SectionResult(section, worst([r.finding.status for r in results]), results)


def fence(text: str) -> str:
    return "```text\n" + text.replace("```", "'''") + "\n```"


def render_details(finding: Finding, limit: int) -> list[str]:
    if not finding.details or limit <= 0:
        return []
    if finding.details_format == DetailsFormat.MARKDOWN:
        body = (
            finding.details
            if len(finding.details) <= limit
            else fence(tail(finding.details, limit))
        )
    else:
        body = fence(tail(finding.details, limit))
    return ["", f"<details><summary>{finding.details_title}</summary>", "", body, "", "</details>"]


def duration(seconds: float) -> str:
    return f" _({seconds:.1f}s)_" if seconds >= 0.1 else ""


def render_section(result: SectionResult, limit: int) -> list[str]:
    title = f"{result.section.area} · {result.section.title}"
    lines = ["", f"### {result.status} {title}", ""]
    multiple = len(result.results) > 1
    for item in result.results:
        name = item.check.label or item.check.analysis
        label = f"- {item.finding.status} **{name}**: " if multiple else ""
        lines.append(f"{label}{item.finding.summary}{duration(item.seconds)}")
        lines += render_details(item.finding, limit)
    return lines


def one_line(result: SectionResult) -> str:
    if len(result.results) == 1:
        return result.results[0].finding.summary.replace("|", "\\|")
    return " · ".join(
        f"{item.check.label or item.check.analysis}: {item.finding.status}"
        for item in result.results
    )


def verdict(results: list[SectionResult]) -> str:
    failed = sum(r.status == Status.FAILED for r in results)
    warnings = sum(r.status == Status.WARNING for r in results)
    skipped = sum(r.status == Status.SKIPPED for r in results)
    if failed:
        return f"❌ **Failed**: {plural(failed, 'section failed', 'sections failed')}"
    if warnings:
        return (
            f"⚠️ **Passed with warnings**: {plural(warnings, 'section', 'sections')} with warnings"
        )
    extra = f" ({plural(skipped, 'section', 'sections')} not run)" if skipped else ""
    return "✅ **All good**" + extra


def render_with_limit(results: list[SectionResult], footer: str, limit: int) -> str:
    lines = [MARKER, "## 🔍 Quality Report", "", verdict(results), ""]
    lines += ["| Area | Analysis | Status | Result |", "| --- | --- | --- | --- |"]
    lines += [
        f"| {r.section.area} | {r.section.title} | {r.status} | {one_line(r)} |" for r in results
    ]
    for result in results:
        lines += render_section(result, limit)
    if limit < MAX_DETAILS_CHARS:
        lines += [
            "",
            "_Details were trimmed to fit in a comment: see the job summary of each job._",
        ]
    lines += [
        "",
        "---",
        "This report only informs: each CI job is still the gate for its own checks.",
    ]
    if footer:
        lines.append(footer)
    return "\n".join(lines) + "\n"


def render(
    fragments: dict[Analysis, Fragment],
    job_results: dict[str, str],
    footer: str = "",
) -> str:
    results = [evaluate(section, fragments, job_results) for section in SECTIONS]
    report = render_with_limit(results, footer, MAX_DETAILS_CHARS)
    for limit in REDUCED_DETAILS_CHARS:
        if len(report) <= MAX_REPORT_CHARS:
            break
        report = render_with_limit(results, footer, limit)
    return report


def load_fragments(directory: Path) -> dict[Analysis, Fragment]:
    fragments: dict[Analysis, Fragment] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            fragment = Fragment.read(path)
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
            logger.warning("ignoring invalid fragment %s: %s", path, error)
            continue
        fragments[fragment.analysis] = fragment
    return fragments


def parse_job_results(needs_json: str) -> dict[str, str]:
    if not needs_json:
        return {}
    needs = json.loads(needs_json)
    return {job: str(data.get("result", "unknown")) for job, data in needs.items()}


def run_command(analysis: Analysis, command: list[str], directory: Path, advisory: bool) -> int:
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
    except OSError as error:
        message = f"could not run {command[0]}: {error}"
        logger.error(message)
        Fragment(analysis, 127, message, advisory).write(directory)
        return 127
    assert process.stdout is not None
    lines: list[str] = []
    for line in process.stdout:
        sys.stdout.write(line)
        lines.append(line)
    exit_code = process.wait()
    # Absolute checkout paths only add noise (and differ between machines).
    output = "".join(lines).replace(f"{Path.cwd()}/", "")
    Fragment(analysis, exit_code, output, advisory, time.monotonic() - started).write(directory)
    return 0 if advisory else exit_code


def footer_from_environment() -> str:
    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not repository or not run_id:
        return ""
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    sha = os.environ.get("QUALITY_REPORT_SHA", os.environ.get("GITHUB_SHA", ""))[:7]
    commit = f"commit `{sha}` · " if sha else ""
    return f"{commit}[CI run]({server}/{repository}/actions/runs/{run_id})"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consolidated CI Quality Report.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run a command and store its output as a fragment")
    run.add_argument("analysis", type=Analysis)
    run.add_argument("--dir", type=Path, default=DEFAULT_DIRECTORY)
    run.add_argument("--advisory", action="store_true", help="never fail, only report")
    render_parser = commands.add_parser("render", help="build the Markdown report")
    render_parser.add_argument("--dir", type=Path, default=DEFAULT_DIRECTORY)
    render_parser.add_argument("--needs-json", default="")
    render_parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    command: list[str] = []
    if "--" in argv:
        separator = argv.index("--")
        argv, command = argv[:separator], argv[separator + 1 :]
    args = build_parser().parse_args(argv)
    if args.command == "run":
        if not command:
            logger.error("missing command after --")
            return 2
        return run_command(args.analysis, command, args.dir, args.advisory)
    report = render(
        load_fragments(args.dir), parse_job_results(args.needs_json), footer_from_environment()
    )
    if args.output:
        args.output.write_text(report)
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
