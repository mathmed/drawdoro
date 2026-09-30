import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger(__name__)

MUTANTS_DIR = Path("mutants")


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


@dataclass
class Tally:
    counts: dict[Outcome, int] = field(default_factory=lambda: defaultdict(int))
    survivors: list[str] = field(default_factory=list)

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


def module_of(meta: Path) -> str:
    return str(meta.relative_to(MUTANTS_DIR)).removesuffix(".meta")


def package_of(module: str) -> str:
    parts = module.split("/")
    return "/".join(parts[:4]) if parts[2] == "usecases" else module


def collect(mutants_dir: Path) -> dict[str, Tally]:
    tallies: dict[str, Tally] = defaultdict(Tally)
    for meta in sorted(mutants_dir.rglob("*.py.meta")):
        exit_codes: dict[str, int | None] = json.loads(meta.read_text())["exit_code_by_key"]
        tally = tallies[module_of(meta)]
        for name, code in exit_codes.items():
            outcome = OUTCOME_BY_EXIT_CODE.get(code, Outcome.OTHER)
            tally.counts[outcome] += 1
            if outcome in (Outcome.SURVIVED, Outcome.NO_TESTS):
                tally.survivors.append(name)
    return tallies


def merge(tallies: dict[str, Tally], key: str) -> dict[str, Tally]:
    merged: dict[str, Tally] = defaultdict(Tally)
    for module, tally in tallies.items():
        target = merged[key if key else package_of(module)]
        for outcome, count in tally.counts.items():
            target.counts[outcome] += count
        target.survivors.extend(tally.survivors)
    return merged


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
    return str(get_diff_for_mutant(name))


def survivors_section(tallies: dict[str, Tally], limit: int) -> list[str]:
    lines = ["### Surviving mutants", ""]
    for module, tally in sorted(tallies.items()):
        if not tally.survivors:
            continue
        lines.append(f"<details><summary><code>{module}</code>: {len(tally.survivors)}</summary>")
        lines.append("")
        for name in tally.survivors[:limit]:
            diff = diff_of(name)
            lines.append(f"`{name}`")
            if diff:
                lines.extend(["```diff", diff.strip(), "```"])
        if len(tally.survivors) > limit:
            lines.append(f"... and {len(tally.survivors) - limit} more (`mutmut results`)")
        lines.extend(["", "</details>", ""])
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarise a mutmut run as Markdown.")
    parser.add_argument("--diffs-per-module", type=int, default=10)
    parser.add_argument("--min-score", type=float, default=0.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    tallies = collect(MUTANTS_DIR)
    if not tallies:
        logger.error("No mutmut results in %s/: run `make mutation` first.", MUTANTS_DIR)
        return 1
    overall = merge(tallies, "all mutated code")["all mutated code"]
    lines = [
        "## Mutation testing",
        "",
        f"**Score: {overall.score:.1f}%** ({overall.detected} of {overall.total} mutants killed; "
        f"{overall.counts[Outcome.SURVIVED]} survived, {overall.counts[Outcome.NO_TESTS]} "
        "without any test).",
        "",
        *table("By package", merge(tallies, "")),
        *table("By file", tallies),
        *survivors_section(tallies, args.diffs_per_module),
    ]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0 if overall.score >= args.min_score else 2


if __name__ == "__main__":
    sys.exit(main())
