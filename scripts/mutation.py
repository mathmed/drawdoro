import argparse
import ast
import fnmatch
import json
import logging
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import tomllib
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger(__name__)

MUTANTS_DIR = Path("mutants")
PYPROJECT = Path("pyproject.toml")
# Ratchet for the PR job: a floor below the current baseline that the owner raises over time.
# Overridden by the MUTATION_MIN_SCORE environment variable (repository variable in CI).
DEFAULT_MIN_SCORE = 60.0
MIN_SCORE_ENV = "MUTATION_MIN_SCORE"
# Machine-readable line read by scripts/quality_report.py (keep the prefix in sync)
RESULT_PREFIX = "MUTATION_RESULT: "
# Printed by `mutmut run` when none of the given mutant name patterns match a mutant
NOTHING_MATCHED = "Filtered for specific mutants, but nothing matches"
MAX_REPORTED_DIFFS = 20
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@", re.MULTILINE)
MUTANT_NAME = re.compile(r"^(?P<module>.+?)\.(?P<function>xǁ[^.]+|x_[^.]+)__mutmut_\d+$")


class Outcome(StrEnum):
    KILLED = "killed"
    SURVIVED = "survived"
    NO_TESTS = "no tests"
    TIMEOUT = "timeout"
    OTHER = "other"


# Same meaning as mutmut's own status table (mutmut/stats.py); timeouts and type-check failures
# mean the tests noticed the mutant, so they count as killed in the score.
OUTCOME_BY_EXIT_CODE: dict[int | None, Outcome] = {
    0: Outcome.SURVIVED,
    1: Outcome.KILLED,
    3: Outcome.KILLED,
    37: Outcome.KILLED,
    5: Outcome.NO_TESTS,
    33: Outcome.NO_TESTS,
    24: Outcome.TIMEOUT,
    -24: Outcome.TIMEOUT,
    36: Outcome.TIMEOUT,
    152: Outcome.TIMEOUT,
    255: Outcome.TIMEOUT,
}
UNDETECTED = (Outcome.SURVIVED, Outcome.NO_TESTS, Outcome.OTHER)


@dataclass
class Tally:
    counts: dict[Outcome, int] = field(default_factory=lambda: defaultdict(int))
    survivors: list[str] = field(default_factory=list)
    outcomes: dict[str, Outcome] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    @property
    def detected(self) -> int:
        return self.counts[Outcome.KILLED] + self.counts[Outcome.TIMEOUT]

    # Mutants no test runs count as survivors: nothing would catch that change.
    @property
    def score(self) -> float:
        return 100 * self.detected / self.total if self.total else 100.0

    def add(self, name: str, outcome: Outcome) -> None:
        self.counts[outcome] += 1
        self.outcomes[name] = outcome
        if outcome in UNDETECTED:
            self.survivors.append(name)


def module_of(meta: Path, mutants_dir: Path) -> str:
    return str(meta.relative_to(mutants_dir)).removesuffix(".meta")


def package_of(module: str) -> str:
    parts = module.split("/")
    return "/".join(parts[:4]) if len(parts) > 3 and parts[2] == "usecases" else module


def matches(name: str, patterns: list[str] | None) -> bool:
    return patterns is None or any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def collect(mutants_dir: Path, patterns: list[str] | None = None) -> dict[str, Tally]:
    tallies: dict[str, Tally] = defaultdict(Tally)
    for meta in sorted(mutants_dir.rglob("*.py.meta")):
        exit_codes: dict[str, int | None] = json.loads(meta.read_text())["exit_code_by_key"]
        for name, code in exit_codes.items():
            if not matches(name, patterns):
                continue
            tallies[module_of(meta, mutants_dir)].add(
                name, OUTCOME_BY_EXIT_CODE.get(code, Outcome.OTHER)
            )
    return dict(tallies)


def merge(tallies: dict[str, Tally], key: str) -> dict[str, Tally]:
    merged: dict[str, Tally] = defaultdict(Tally)
    for module, tally in tallies.items():
        target = merged[key if key else package_of(module)]
        for name, outcome in tally.outcomes.items():
            target.add(name, outcome)
    return dict(merged)


def overall(tallies: dict[str, Tally]) -> Tally:
    return merge(tallies, "all").get("all", Tally())


def table(title: str, tallies: dict[str, Tally]) -> list[str]:
    rows = [
        f"| `{name}` | {t.total} | {t.detected} | {t.counts[Outcome.SURVIVED]} "
        f"| {t.counts[Outcome.NO_TESTS]} | {t.score:.1f}% |"
        for name, t in sorted(tallies.items(), key=lambda item: (item[1].score, item[0]))
    ]
    header = "| Module | Mutants | Killed | Survived | No tests | Score |"
    return [f"### {title}", "", header, "|---|---:|---:|---:|---:|---:|", *rows, ""]


def diff_of(name: str) -> str | None:
    try:
        from mutmut.mutation.diff_apply import get_diff_for_mutant
    except ImportError:
        return None
    try:
        return str(get_diff_for_mutant(name)).strip()
    except (OSError, ValueError, KeyError) as error:
        logger.warning("could not diff %s: %s", name, error)
        return None


def survivors_section(tallies: dict[str, Tally], limit: int) -> list[str]:
    lines = ["### Surviving mutants", ""]
    for module, tally in sorted(tallies.items()):
        if tally.survivors:
            lines += module_survivors(module, tally.survivors, limit)
    return lines


def module_survivors(module: str, survivors: list[str], limit: int) -> list[str]:
    lines = [f"<details><summary><code>{module}</code>: {len(survivors)}</summary>", ""]
    for name in survivors[:limit]:
        lines += survivor_lines(name)
    if len(survivors) > limit:
        lines.append(f"... and {len(survivors) - limit} more (`mutmut results`)")
    lines.extend(["", "</details>", ""])
    return lines


def survivor_lines(name: str) -> list[str]:
    diff = diff_of(name)
    return [f"`{name}`", "```diff", diff, "```"] if diff else [f"`{name}`"]


def full_report(tallies: dict[str, Tally], diffs_per_module: int) -> str:
    total = overall(tallies)
    lines = [
        "## Mutation testing",
        "",
        f"**Score: {total.score:.1f}%** ({total.detected} of {total.total} mutants killed; "
        f"{total.counts[Outcome.SURVIVED]} survived, {total.counts[Outcome.NO_TESTS]} "
        "without any test).",
        "",
        *table("By package", merge(tallies, "")),
        *table("By file", tallies),
        *survivors_section(tallies, diffs_per_module),
    ]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class FunctionSpan:
    mangled: str
    start: int
    end: int

    def contains(self, line: int) -> bool:
        return self.start <= line <= self.end


def span_of(node: ast.FunctionDef | ast.AsyncFunctionDef, mangled: str) -> FunctionSpan:
    start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    return FunctionSpan(mangled, start, node.end_lineno or node.lineno)


# Mirrors how mutmut names what it mutates: top-level functions (x_name) and methods of top-level
# classes (xǁClassǁmethod). Nested functions belong to the function that contains them.
def function_spans(tree: ast.Module) -> list[FunctionSpan]:
    spans: list[FunctionSpan] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            spans.append(span_of(node, f"x_{node.name}"))
        if isinstance(node, ast.ClassDef):
            spans += method_spans(node)
    return spans


def method_spans(node: ast.ClassDef) -> list[FunctionSpan]:
    return [
        span_of(item, f"xǁ{node.name}ǁ{item.name}")
        for item in node.body
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


# Lines whose change cannot alter what a function does: imports, blank lines and comments.
def neutral_lines(tree: ast.Module, source: str) -> set[int]:
    return blank_or_comment_lines(source) | import_lines(tree)


def blank_or_comment_lines(source: str) -> set[int]:
    return {
        number
        for number, text in enumerate(source.splitlines(), start=1)
        if is_blank_or_comment(text)
    }


def is_blank_or_comment(text: str) -> bool:
    stripped = text.strip()
    return not stripped or stripped.startswith("#")


def import_lines(tree: ast.Module) -> set[int]:
    lines: set[int] = set()
    for node in tree.body:
        if isinstance(node, ast.Import | ast.ImportFrom):
            lines.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return lines


def module_name(file: str) -> str:
    return file.removesuffix(".py").replace("/", ".")


def targets_for_file(file: str, source: str, lines: set[int]) -> list[str]:
    tree = ast.parse(source)
    spans = function_spans(tree)
    module = module_name(file)
    relevant = lines - neutral_lines(tree, source)
    if not relevant:
        return []
    touched = touched_spans(spans, relevant)
    # A change outside functions (constants, class attributes...) can affect all of them.
    if changes_outside(spans, relevant) or len(touched) == len(spans):
        return [f"{module}.*"]
    return [f"{module}.{span.mangled}__mutmut_*" for span in touched]


def touched_spans(spans: list[FunctionSpan], lines: set[int]) -> list[FunctionSpan]:
    return [span for span in spans if any(span.contains(line) for line in lines)]


def changes_outside(spans: list[FunctionSpan], lines: set[int]) -> bool:
    return any(not any(span.contains(line) for span in spans) for line in lines)


def parse_changed_lines(diff: str) -> set[int]:
    lines: set[int] = set()
    for hunk in HUNK_HEADER.finditer(diff):
        start = int(hunk["start"])
        count = int(hunk["count"]) if hunk["count"] is not None else 1
        # A pure deletion (count 0) sits between line `start` and the next one.
        lines.update(range(start, start + count) if count else (start, start + 1))
    return lines


def load_scope(pyproject: Path = PYPROJECT) -> list[str]:
    config = tomllib.loads(pyproject.read_text())["tool"]["mutmut"]
    return list(config.get("only_mutate", config["source_paths"]))


def in_scope(file: str, scope: list[str]) -> bool:
    if not file.endswith(".py") or file.endswith("__init__.py"):
        return False
    return any(fnmatch.fnmatch(file, pattern) for pattern in scope)


# Fixed git and mutmut command lines with no shell: the only arguments are the base ref and file
# names that come from git itself, and the mutant name patterns built from them.
def git(*args: str) -> str:
    command = [executable("git"), *args]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout  # nosec B603


def executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FileNotFoundError(f"{name} is not on the PATH")
    return path


def changed_targets(base_ref: str, scope: list[str]) -> list[str]:
    files = git("diff", "--name-only", "--diff-filter=AMR", f"{base_ref}...HEAD").splitlines()
    targets: list[str] = []
    for file in sorted(f for f in files if in_scope(f, scope)):
        lines = parse_changed_lines(git("diff", "-U0", f"{base_ref}...HEAD", "--", file))
        targets += targets_for_file(file, Path(file).read_text(), lines)
    return targets


def location_of(name: str) -> tuple[str, str]:
    match = MUTANT_NAME.match(name)
    if not match:
        return name, name
    function = match["function"]
    readable = function.removeprefix("xǁ").replace("ǁ", ".") if "ǁ" in function else function[2:]
    return match["module"].replace(".", "/") + ".py", readable


@dataclass(frozen=True)
class Survivor:
    file: str
    function: str
    status: str
    name: str
    diff: str


@dataclass(frozen=True)
class FileScore:
    file: str
    total: int
    killed: int
    score: float


@dataclass(frozen=True)
class ChangedReport:
    tallies: dict[str, Tally]
    min_score: float
    targets: list[str]

    @property
    def total(self) -> Tally:
        return overall(self.tallies)

    @property
    def passed(self) -> bool:
        return self.total.score >= self.min_score

    def survivors(self) -> list[Survivor]:
        items: list[Survivor] = []
        for _, tally in sorted(self.tallies.items()):
            for name in tally.survivors:
                file, function = location_of(name)
                diff = diff_of(name) if len(items) < MAX_REPORTED_DIFFS else None
                items.append(Survivor(file, function, tally.outcomes[name].value, name, diff or ""))
        return items

    def to_result_line(self) -> str:
        total = self.total
        return RESULT_PREFIX + json.dumps(
            {
                "skipped": False,
                "reason": "",
                "score": total.score,
                "min_score": self.min_score,
                "killed": total.detected,
                "total": total.total,
                "targets": self.targets,
                "files": [
                    asdict(FileScore(file, t.total, t.detected, t.score))
                    for file, t in sorted(self.tallies.items())
                ],
                "survivors": [asdict(survivor) for survivor in self.survivors()],
            }
        )

    def to_markdown(self) -> str:
        total = self.total
        verdict = "✅ passed" if self.passed else "❌ below the ratchet"
        lines = [
            "## Mutation testing (changed domain code)",
            "",
            f"**Score: {total.score:.1f}%** (ratchet {self.min_score:.1f}%, {verdict}): "
            f"{total.detected} of {total.total} mutants killed.",
            "",
            *table("By file", self.tallies),
            *survivors_list(self.tallies),
        ]
        return "\n".join(lines) + "\n"


def survivors_list(tallies: dict[str, Tally]) -> list[str]:
    survivors = [name for tally in tallies.values() for name in tally.survivors]
    if not survivors:
        return []
    names = [f"- `{name}`" for name in survivors]
    return ["### Survivors", "", *names, "", "Inspect one with `uv run mutmut show <name>`."]


def skipped_result_line(min_score: float, reason: str) -> str:
    return RESULT_PREFIX + json.dumps(
        {
            "skipped": True,
            "reason": reason,
            "score": 100.0,
            "min_score": min_score,
            "killed": 0,
            "total": 0,
            "targets": [],
            "files": [],
            "survivors": [],
        }
    )


def min_score() -> float:
    return float(os.environ.get(MIN_SCORE_ENV) or DEFAULT_MIN_SCORE)


def publish(markdown: str) -> None:
    sys.stdout.write(markdown)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    with open(summary, "a") as handle:
        handle.write(markdown)


def run_mutmut(targets: list[str]) -> tuple[int, str]:
    process = subprocess.Popen(  # nosec B603
        [executable("mutmut"), "run", *targets],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    lines: list[str] = []
    for line in process.stdout or ():
        sys.stdout.write(line)
        lines.append(line)
    return process.wait(), "".join(lines)


def skip(reason: str, threshold: float) -> int:
    publish(f"## Mutation testing (changed domain code)\n\n{reason}\n")
    sys.stdout.write(skipped_result_line(threshold, reason) + "\n")
    return 0


def changed_command(base_ref: str) -> int:
    threshold = min_score()
    targets = changed_targets(base_ref, load_scope())
    if not targets:
        return skip("No use case or domain service changed, nothing to mutate.", threshold)
    sys.stdout.write("Mutating:\n" + "".join(f"  {target}\n" for target in targets))
    sys.stdout.flush()
    exit_code, output = run_mutmut(targets)
    if exit_code != 0:
        return mutmut_failure(exit_code, output, threshold)
    report = ChangedReport(collect(MUTANTS_DIR, targets), threshold, targets)
    publish(report.to_markdown())
    sys.stdout.write(report.to_result_line() + "\n")
    return 0 if report.passed else 1


def mutmut_failure(exit_code: int, output: str, threshold: float) -> int:
    if NOTHING_MATCHED in output:
        return skip("The changed functions produce no mutants.", threshold)
    logger.error("mutmut run failed with exit code %s", exit_code)
    return exit_code


def report_command(diffs_per_module: int, threshold: float) -> int:
    tallies = collect(MUTANTS_DIR)
    if not tallies:
        logger.error("No mutmut results in %s/: run `make mutation` first.", MUTANTS_DIR)
        return 1
    sys.stdout.write(full_report(tallies, diffs_per_module))
    return 0 if overall(tallies).score >= threshold else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mutation testing helpers around mutmut.")
    commands = parser.add_subparsers(dest="command", required=True)
    changed = commands.add_parser("changed", help="mutate only the domain code changed vs BASE")
    changed.add_argument("--base", default="origin/main")
    report = commands.add_parser("report", help="summarise a full mutmut run as Markdown")
    report.add_argument("--diffs-per-module", type=int, default=10)
    report.add_argument("--min-score", type=float, default=0.0)
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args()
    if args.command == "changed":
        return changed_command(args.base)
    return report_command(args.diffs_per_module, args.min_score)


if __name__ == "__main__":
    sys.exit(main())
