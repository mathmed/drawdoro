import argparse
import json
import logging
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import TextIO

import yaml

logger = logging.getLogger(__name__)

DEFAULT_FLOORS = Path(".github/risk-floors.yaml")
LABEL_PREFIX = "risk:"
STDIN = "-"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return list(RiskLevel).index(self)

    @property
    def label(self) -> str:
        return f"{LABEL_PREFIX}{self.value}"


class RiskFloorError(Exception):
    pass


@dataclass(frozen=True)
class Floor:
    category: str
    level: RiskLevel
    patterns: tuple[str, ...]

    def matches(self, file: str) -> bool:
        path = PurePosixPath(file)
        return any(path.full_match(pattern) for pattern in self.patterns)


@dataclass(frozen=True)
class FloorHit:
    category: str
    level: RiskLevel
    files: tuple[str, ...]


@dataclass(frozen=True)
class Assessment:
    hits: tuple[FloorHit, ...]

    @property
    def floor(self) -> RiskLevel:
        return max(
            (hit.level for hit in self.hits), key=lambda level: level.rank, default=RiskLevel.LOW
        )

    def describe(self) -> str:
        lines = [f"Risk floor: {self.floor}"]
        lines += [f"- {hit.category} ({hit.level}): {', '.join(hit.files)}" for hit in self.hits]
        if not self.hits:
            lines.append("- no file matches a floor category")
        return "\n".join(lines)


def floor_level(category: str, level: object) -> RiskLevel:
    if level not in set(RiskLevel):
        raise RiskFloorError(f"unknown level {level!r} in floor {category!r}")
    return RiskLevel(str(level))


def floor_patterns(entry: dict[str, object]) -> tuple[str, ...]:
    paths = entry.get("paths")
    if not isinstance(paths, list) or not paths:
        raise RiskFloorError(f"each floor needs a non-empty list of paths: {entry!r}")
    return tuple(str(path) for path in paths)


def parse_floor(entry: object) -> Floor:
    if not isinstance(entry, dict):
        raise RiskFloorError(f"each floor must be a mapping, got: {entry!r}")
    category = entry.get("category")
    if not isinstance(category, str):
        raise RiskFloorError(f"each floor needs a category: {entry!r}")
    return Floor(category, floor_level(category, entry.get("level")), floor_patterns(entry))


def load_floors(path: Path) -> tuple[Floor, ...]:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or not isinstance(data.get("floors"), list):
        raise RiskFloorError(f"{path} must have a top-level `floors` list")
    return tuple(parse_floor(entry) for entry in data["floors"])


def assess(files: list[str], floors: tuple[Floor, ...]) -> Assessment:
    hits = []
    for floor in floors:
        matched = tuple(file for file in files if floor.matches(file))
        if matched:
            hits.append(FloorHit(floor.category, floor.level, matched))
    return Assessment(tuple(hits))


# One repository-relative path per line, as `git diff --name-only --no-renames` prints them (both
# sides of a rename, so moving a file out of a floor path counts too).
def parse_changed_files(text: str) -> list[str]:
    return sorted({line.strip() for line in text.splitlines() if line.strip()})


def read_changed_files(source: str, stdin: TextIO) -> list[str]:
    text = stdin.read() if source == STDIN else Path(source).read_text()
    return parse_changed_files(text)


def risk_labels(labels: list[str]) -> list[str]:
    return [label for label in labels if label.startswith(LABEL_PREFIX)]


def valid_labels() -> str:
    return ", ".join(level.label for level in RiskLevel)


def level_problem(label: str, floor: RiskLevel) -> str | None:
    if label not in {level.label for level in RiskLevel}:
        return f"unknown risk label {label}: use one of {valid_labels()}"
    if RiskLevel(label.removeprefix(LABEL_PREFIX)).rank < floor.rank:
        return f"{label} is below the floor of this PR ({floor.label})"
    return None


def label_problem(labels: list[str], floor: RiskLevel) -> str | None:
    found = risk_labels(labels)
    if len(found) != 1:
        return f"expected exactly one risk label ({valid_labels()}), found: {found or 'none'}"
    return level_problem(found[0], floor)


def parse_labels(labels_json: str) -> list[str]:
    labels = json.loads(labels_json or "[]")
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise RiskFloorError(f"--labels-json must be a JSON list of strings, got: {labels_json}")
    return labels


def floor_command(files: list[str], floors_path: Path) -> int:
    logger.info("%s", assess(files, load_floors(floors_path)).describe())
    return 0


def check_command(files: list[str], floors_path: Path, labels_json: str) -> int:
    assessment = assess(files, load_floors(floors_path))
    logger.info("%s", assessment.describe())
    problem = label_problem(parse_labels(labels_json), assessment.floor)
    if problem:
        logger.error("Risk label check failed: %s.", problem)
        return 1
    logger.info("Risk label is at or above the floor.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Risk floor of a change and its risk label.")
    parser.add_argument("--floors", type=Path, default=DEFAULT_FLOORS)
    parser.add_argument(
        "--changed-files",
        required=True,
        help="file with the changed paths, one per line (`-` reads them from stdin)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("floor", help="print the risk floor of the changed files")
    check = commands.add_parser("check", help="fail when the PR's risk label is below the floor")
    check.add_argument("--labels-json", required=True)
    return parser


def main(argv: list[str], stdin: TextIO = sys.stdin) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    args = build_parser().parse_args(argv)
    try:
        files = read_changed_files(args.changed_files, stdin)
        if args.command == "floor":
            return floor_command(files, args.floors)
        return check_command(files, args.floors, args.labels_json)
    except (RiskFloorError, OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        logger.error("Risk label check failed: %s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
