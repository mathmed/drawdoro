import argparse
import ast
import io
import json
import logging
import re
import sys
import tokenize
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_BASELINE = Path("suppressions-baseline.json")
# Every tree with code a person or an agent writes: the API and its migrations, the MCP server, the
# scripts, the tests and the frontend. A missing root fails the check instead of scanning less.
DEFAULT_ROOTS = (
    Path("app"),
    Path("alembic"),
    Path("mcp"),
    Path("scripts"),
    Path("tests"),
    Path("frontend"),
)
# Installed packages, caches and build output are not ours; hidden directories (.venv...) neither.
SKIPPED_DIRECTORIES = {"node_modules", "__pycache__", "dist", "coverage"}
PYTHON_SUFFIXES = {".py"}
TYPESCRIPT_SUFFIXES = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}
# Machine-readable line read by scripts/quality_report.py (keep the prefix in sync)
RESULT_PREFIX = "SUPPRESSIONS_RESULT: "


class Kind(StrEnum):
    NOQA = "noqa"
    TYPE_IGNORE = "type-ignore"
    NOSEC = "nosec"
    NO_COVER = "no-cover"
    PYLINT = "pylint-disable"
    MYPY = "mypy-directive"
    PYRIGHT = "pyright-directive"
    FORMATTER = "formatter-off"
    ESLINT_DISABLE = "eslint-disable"
    TS_IGNORE = "ts-ignore"
    TS_EXPECT_ERROR = "ts-expect-error"
    TS_NOCHECK = "ts-nocheck"
    TEST_SKIP = "test-skip"
    TEST_ONLY = "test-only"
    TEST_XFAIL = "test-xfail"


PYTHON_COMMENT_PATTERNS: tuple[tuple[Kind, re.Pattern[str]], ...] = (
    (Kind.NOQA, re.compile(r"\bnoqa\b", re.IGNORECASE)),
    (Kind.TYPE_IGNORE, re.compile(r"\btype:\s*ignore\b")),
    (Kind.NOSEC, re.compile(r"\bnosec\b", re.IGNORECASE)),
    (Kind.NO_COVER, re.compile(r"\bpragma:\s*no\s*(?:cover|branch)\b", re.IGNORECASE)),
    (Kind.PYLINT, re.compile(r"\bpylint:\s*disable", re.IGNORECASE)),
    (Kind.MYPY, re.compile(r"\bmypy:")),
    (Kind.PYRIGHT, re.compile(r"\bpyright:")),
    (Kind.FORMATTER, re.compile(r"\b(?:fmt|isort|yapf):\s*(?:off|skip|skip_file|disable)\b")),
)
MARK_ATTRIBUTES = {"skip": Kind.TEST_SKIP, "skipif": Kind.TEST_SKIP, "xfail": Kind.TEST_XFAIL}
PYTEST_FUNCTIONS = {
    "skip": Kind.TEST_SKIP,
    "importorskip": Kind.TEST_SKIP,
    "xfail": Kind.TEST_XFAIL,
}
UNITTEST_DECORATORS = {
    "skip": Kind.TEST_SKIP,
    "skipIf": Kind.TEST_SKIP,
    "skipUnless": Kind.TEST_SKIP,
    "expectedFailure": Kind.TEST_XFAIL,
}
SKIP_METHODS = {"skipTest": Kind.TEST_SKIP}
OWNER_ATTRIBUTES = {
    "mark": MARK_ATTRIBUTES,
    "pytest": PYTEST_FUNCTIONS,
    "unittest": UNITTEST_DECORATORS,
}
IMPORTABLE = {"pytest": PYTEST_FUNCTIONS, "unittest": UNITTEST_DECORATORS}

# Directives only count right after a comment opener (`//`, `/*`, `{/*` in JSX), where the tools
# read them.
COMMENT_OPENER = r"(?://|/\*)\s*"
TYPESCRIPT_COMMENT_PATTERNS: tuple[tuple[Kind, re.Pattern[str]], ...] = (
    (Kind.ESLINT_DISABLE, re.compile(COMMENT_OPENER + r"eslint-disable(?:-next-line|-line)?\b")),
    # Inline rule configuration (`/* eslint no-console: "off" */`) turns rules off too
    (Kind.ESLINT_DISABLE, re.compile(r"/\*\s*eslint\s+[@\w/-]+\s*:")),
    (Kind.TS_IGNORE, re.compile(COMMENT_OPENER + r"@ts-ignore\b")),
    (Kind.TS_EXPECT_ERROR, re.compile(COMMENT_OPENER + r"@ts-expect-error\b")),
    (Kind.TS_NOCHECK, re.compile(COMMENT_OPENER + r"@ts-nocheck\b")),
    (Kind.NO_COVER, re.compile(COMMENT_OPENER + r"(?:istanbul|v8|c8)\s+ignore\b")),
    (Kind.FORMATTER, re.compile(COMMENT_OPENER + r"prettier-ignore\b")),
)
TEST_MARKERS = {
    "skip": Kind.TEST_SKIP,
    "skipIf": Kind.TEST_SKIP,
    "runIf": Kind.TEST_SKIP,
    "todo": Kind.TEST_SKIP,
    "xit": Kind.TEST_SKIP,
    "xtest": Kind.TEST_SKIP,
    "xdescribe": Kind.TEST_SKIP,
    "only": Kind.TEST_ONLY,
    "fit": Kind.TEST_ONLY,
    "ftest": Kind.TEST_ONLY,
    "fdescribe": Kind.TEST_ONLY,
    "fails": Kind.TEST_XFAIL,
}
TYPESCRIPT_TEST_PATTERNS: tuple[re.Pattern[str], ...] = (
    # it.skip, describe.only, test.concurrent.skipIf(...), it.fails, ctx.skip()...
    re.compile(
        r"\b(?:describe|it|test|suite|bench)"
        r"(?:\.(?:concurrent|sequential|shuffle|each|for|extend|scoped))*"
        r"\.(?P<marker>skip|skipIf|runIf|todo|only|fails)\b"
    ),
    re.compile(r"\b(?:ctx|context)\.(?P<marker>skip)\s*\("),
    # Jasmine-style aliases: xit, xdescribe, fit, fdescribe...
    re.compile(r"(?<![\w.$])(?P<marker>xit|xtest|xdescribe|fit|ftest|fdescribe)\s*\("),
)


@dataclass(frozen=True)
class Occurrence:
    path: str
    line: int
    kind: Kind


@dataclass(frozen=True)
class Change:
    path: str
    kind: Kind
    baseline: int
    current: int
    lines: tuple[int, ...]

    @property
    def is_increase(self) -> bool:
        return self.current > self.baseline


@dataclass(frozen=True)
class Comparison:
    occurrences: tuple[Occurrence, ...]
    baseline: Counter[tuple[str, Kind]]

    @property
    def current(self) -> Counter[tuple[str, Kind]]:
        return Counter((item.path, item.kind) for item in self.occurrences)

    @property
    def changes(self) -> tuple[Change, ...]:
        current = self.current
        keys = sorted(set(current) | set(self.baseline))
        return tuple(
            self.change_for(path, kind, current[(path, kind)])
            for path, kind in keys
            if current[(path, kind)] != self.baseline[(path, kind)]
        )

    @property
    def increases(self) -> tuple[Change, ...]:
        return tuple(change for change in self.changes if change.is_increase)

    @property
    def decreases(self) -> tuple[Change, ...]:
        return tuple(change for change in self.changes if not change.is_increase)

    def change_for(self, path: str, kind: Kind, current: int) -> Change:
        lines = tuple(
            item.line for item in self.occurrences if item.path == path and item.kind == kind
        )
        return Change(path, kind, self.baseline[(path, kind)], current, lines)

    def to_result_line(self) -> str:
        return RESULT_PREFIX + json.dumps(
            {
                "total": len(self.occurrences),
                "baseline_total": self.baseline.total(),
                "totals": totals_by_kind(self.current),
                "changes": [change_payload(change) for change in self.changes],
            }
        )


def change_payload(change: Change) -> dict[str, object]:
    return {
        "path": change.path,
        "kind": change.kind.value,
        "baseline": change.baseline,
        "current": change.current,
        "lines": list(change.lines),
    }


def totals_by_kind(counts: Counter[tuple[str, Kind]]) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for (_, kind), count in counts.items():
        totals[kind.value] += count
    return {kind.value: totals[kind.value] for kind in Kind if totals[kind.value]}


def python_comment_kinds(source: str) -> Iterator[tuple[int, Kind]]:
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT:
            yield from matches_in(token.string, token.start[0], PYTHON_COMMENT_PATTERNS)


def matches_in(
    text: str, line: int, patterns: tuple[tuple[Kind, re.Pattern[str]], ...]
) -> Iterator[tuple[int, Kind]]:
    for kind, pattern in patterns:
        for _ in pattern.finditer(text):
            yield line, kind


def owner_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def attribute_kind(node: ast.Attribute) -> Kind | None:
    if node.attr in SKIP_METHODS:
        return SKIP_METHODS[node.attr]
    return OWNER_ATTRIBUTES.get(owner_name(node.value), {}).get(node.attr)


def imported_names(tree: ast.Module) -> dict[str, Kind]:
    names: dict[str, Kind] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in IMPORTABLE:
            names |= imported_from(node, IMPORTABLE[node.module])
    return names


def imported_from(node: ast.ImportFrom, functions: dict[str, Kind]) -> dict[str, Kind]:
    return {
        alias.asname or alias.name: functions[alias.name]
        for alias in node.names
        if alias.name in functions
    }


def node_kind(node: ast.AST, names: dict[str, Kind]) -> Kind | None:
    if isinstance(node, ast.Attribute):
        return attribute_kind(node)
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
        return names.get(node.id)
    return None


def skip_marker_kinds(tree: ast.Module) -> Iterator[tuple[int, Kind]]:
    names = imported_names(tree)
    for node in ast.walk(tree):
        kind = node_kind(node, names)
        if kind is not None and isinstance(node, ast.expr):
            yield node.lineno, kind


def scan_python(path: str, source: str) -> list[Occurrence]:
    tree = ast.parse(source, filename=path)
    found = [*python_comment_kinds(source), *skip_marker_kinds(tree)]
    return [Occurrence(path, line, kind) for line, kind in sorted(found)]


def typescript_line_kinds(text: str, line: int) -> Iterator[tuple[int, Kind]]:
    yield from matches_in(text, line, TYPESCRIPT_COMMENT_PATTERNS)
    for pattern in TYPESCRIPT_TEST_PATTERNS:
        for match in pattern.finditer(text):
            yield line, TEST_MARKERS[match["marker"]]


def scan_typescript(path: str, source: str) -> list[Occurrence]:
    found = [
        item
        for number, text in enumerate(source.splitlines(), start=1)
        for item in typescript_line_kinds(text, number)
    ]
    return [Occurrence(path, line, kind) for line, kind in sorted(found)]


def scanner_for(file: Path) -> Callable[[str, str], list[Occurrence]] | None:
    if file.suffix in PYTHON_SUFFIXES:
        return scan_python
    if file.suffix in TYPESCRIPT_SUFFIXES:
        return scan_typescript
    return None


def is_skipped(directory: str) -> bool:
    return directory.startswith(".") or directory in SKIPPED_DIRECTORIES


def kept_directories(names: list[str]) -> list[str]:
    return [name for name in names if not is_skipped(name)]


def files_under(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        raise FileNotFoundError(f"suppression scan root not found: {root}")
    for directory, subdirectories, names in root.walk():
        # Pruned in place, so installed packages and caches are never walked
        subdirectories[:] = kept_directories(subdirectories)
        yield from (directory / name for name in names)


def source_files(roots: Iterable[Path]) -> list[Path]:
    return sorted(file for root in roots for file in files_under(root) if scanner_for(file))


def scan_file(file: Path) -> list[Occurrence]:
    scanner = scanner_for(file)
    if scanner is None:
        return []
    return scanner(file.as_posix(), file.read_text(encoding="utf-8"))


def scan(roots: Iterable[Path]) -> tuple[Occurrence, ...]:
    return tuple(occurrence for file in source_files(roots) for occurrence in scan_file(file))


def load_baseline(path: Path) -> Counter[tuple[str, Kind]]:
    if not path.exists():
        return Counter()
    data = json.loads(path.read_text())
    return Counter(
        {
            (file, Kind(kind)): int(count)
            for file, kinds in data.items()
            for kind, count in kinds.items()
        }
    )


def write_baseline(path: Path, counts: Counter[tuple[str, Kind]]) -> None:
    data: dict[str, dict[str, int]] = {}
    for (file, kind), count in sorted(counts.items()):
        data.setdefault(file, {})[kind.value] = count
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def describe(change: Change) -> str:
    lines = ", ".join(str(line) for line in change.lines) or "-"
    return f"  {change.path}: {change.kind} {change.baseline} -> {change.current} (lines: {lines})"


def log_changes(title: str, changes: tuple[Change, ...]) -> None:
    if changes:
        logger.info("%s\n%s", title, "\n".join(describe(change) for change in changes))


def log_report(comparison: Comparison) -> None:
    logger.info(
        "Suppressions: %s (baseline %s)", len(comparison.occurrences), comparison.baseline.total()
    )
    for kind, count in totals_by_kind(comparison.current).items():
        logger.info("  %s: %s", kind, count)
    log_changes(
        "New suppressions (remove them, or get the owner's approval to raise the baseline):",
        comparison.increases,
    )
    log_changes(
        "Suppressions removed (lock the improvement in with `make suppressions-update`):",
        comparison.decreases,
    )


def check_command(baseline_path: Path, roots: list[Path]) -> int:
    comparison = Comparison(scan(roots), load_baseline(baseline_path))
    log_report(comparison)
    sys.stdout.write(comparison.to_result_line() + "\n")
    sys.stdout.flush()
    if comparison.changes:
        logger.error("Suppressions differ from %s.", baseline_path)
        return 1
    logger.info("Suppressions match the baseline.")
    return 0


def update_command(baseline_path: Path, roots: list[Path], *, can_increase: bool) -> int:
    comparison = Comparison(scan(roots), load_baseline(baseline_path))
    log_report(comparison)
    if comparison.increases and not can_increase:
        logger.error(
            "Refusing to raise the baseline: pass --allow-increase only with the owner's approval."
        )
        return 1
    write_baseline(baseline_path, comparison.current)
    logger.info("Baseline written to %s.", baseline_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Suppression ratchet.")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--root", type=Path, action="append", dest="roots")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="fail when the suppressions differ from the baseline")
    update = commands.add_parser("update", help="rewrite the baseline with the current counts")
    update.add_argument("--allow-increase", action="store_true")
    return parser


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    args = build_parser().parse_args(argv)
    roots = args.roots or list(DEFAULT_ROOTS)
    if args.command == "check":
        return check_command(args.baseline, roots)
    return update_command(args.baseline, roots, can_increase=args.allow_increase)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
