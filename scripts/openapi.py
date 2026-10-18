import argparse
import importlib
import json
import logging
import os
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

APP_MODULE = "app.main.main"
SCRIPT = Path(__file__).resolve()
BASE_SCHEMA = "base.openapi.json"
HEAD_SCHEMA = "head.openapi.json"
BASE_TREE = "base-tree"
GIT_TIMEOUT_SECONDS = 120
# The base export installs the base branch's dependencies into a fresh environment first
EXPORT_TIMEOUT_SECONDS = 600
OASDIFF_TIMEOUT_SECONDS = 120
COMMAND_NOT_FOUND = 127


class OpenApiDiffError(Exception):
    pass


def export_schema(app_dir: Path, output: Path) -> None:
    sys.path.insert(0, str(app_dir))
    module = importlib.import_module(APP_MODULE)
    schema: dict[str, object] = module.app.openapi()
    output.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")


def executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise OpenApiDiffError(f"{name} not found on PATH")
    return path


# The commands are built here from fixed arguments and paths, never from untrusted input, and no
# shell is involved.
def run(
    command: list[str], *, cwd: Path, timeout: int, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # nosec B603
        command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=False
    )


def run_or_fail(
    command: list[str], *, cwd: Path, timeout: int, env: dict[str, str] | None = None
) -> str:
    result = run(command, cwd=cwd, timeout=timeout, env=env)
    if result.returncode != 0:
        raise OpenApiDiffError(f"`{' '.join(command)}` failed:\n{result.stdout}{result.stderr}")
    return result.stdout


def merge_base(base_ref: str, repository: Path) -> str:
    command = [executable("git"), "merge-base", base_ref, "HEAD"]
    try:
        return run_or_fail(command, cwd=repository, timeout=GIT_TIMEOUT_SECONDS).strip()
    except OpenApiDiffError as error:
        message = f"{error}\nIs {base_ref} fetched with its history (fetch-depth: 0)?"
        raise OpenApiDiffError(message) from error


def export_environment() -> dict[str, str]:
    # Each checkout uses its own project environment, not the one this script runs in
    return {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}


# Runs from the temporary directory, so neither side reads a developer's .env (the settings read
# .env from the working directory): both schemas come from the same defaults and environment.
def export_in(checkout: Path, output: Path) -> None:
    command = [executable("uv"), "run", "--project", str(checkout), "--locked", "--no-dev"]
    command += ["--inexact", "python", str(SCRIPT), "export"]
    command += ["--app-dir", str(checkout), "--output", str(output)]
    run_or_fail(
        command, cwd=output.parent, timeout=EXPORT_TIMEOUT_SECONDS, env=export_environment()
    )


def export_base(commit: str, repository: Path, output: Path) -> None:
    tree = output.parent / BASE_TREE
    git = executable("git")
    worktree = [git, "worktree"]
    run_or_fail(
        [*worktree, "add", "--detach", str(tree), commit],
        cwd=repository,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    try:
        export_in(tree, output)
    finally:
        run_or_fail(
            [*worktree, "remove", "--force", str(tree)],
            cwd=repository,
            timeout=GIT_TIMEOUT_SECONDS,
        )


def changelog(oasdiff: str, directory: Path) -> int:
    command = [oasdiff, "changelog", BASE_SCHEMA, HEAD_SCHEMA, "--fail-on", "ERR"]
    command += ["--color", "never", "--allow-external-refs=false"]
    result = run(command, cwd=directory, timeout=OASDIFF_TIMEOUT_SECONDS)
    sys.stdout.write(result.stdout + result.stderr)
    return result.returncode


def diff_command(base_ref: str, oasdiff_name: str, repository: Path) -> int:
    oasdiff = shutil.which(oasdiff_name)
    if oasdiff is None:
        logger.error("oasdiff not found (%s): see docs/DEVELOPMENT.md to install it", oasdiff_name)
        return COMMAND_NOT_FOUND
    commit = merge_base(base_ref, repository)
    logger.info(
        "Comparing the OpenAPI schema of HEAD with %s (merge base %s)", base_ref, commit[:12]
    )
    with tempfile.TemporaryDirectory(prefix="openapi-diff-") as temporary:
        directory = Path(temporary)
        export_in(repository, directory / HEAD_SCHEMA)
        export_base(commit, repository, directory / BASE_SCHEMA)
        return changelog(oasdiff, directory)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenAPI schema export and breaking-change diff.")
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="write the OpenAPI schema of the app")
    export.add_argument("--app-dir", type=Path, default=Path.cwd())
    export.add_argument("--output", type=Path, required=True)
    diff = commands.add_parser("diff", help="fail on breaking changes against the base branch")
    diff.add_argument("--base", default="origin/main")
    diff.add_argument("--oasdiff", default="oasdiff")
    return parser


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    args = build_parser().parse_args(argv)
    if args.command == "export":
        export_schema(args.app_dir.resolve(), args.output.resolve())
        return 0
    try:
        return diff_command(args.base, args.oasdiff, Path.cwd())
    except (OpenApiDiffError, subprocess.TimeoutExpired) as error:
        logger.error("%s", error)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
