import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from scripts import openapi
from scripts.openapi import OpenApiDiffError

REPOSITORY = Path("/repo")
COMMIT = "0123456789abcdef"


def which(name: str) -> str:
    return f"/usr/bin/{name}"


def completed(code: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], code, stdout, stderr)


class TestExport:
    @pytest.fixture(autouse=True)
    def isolated_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "path", list(sys.path))

    def test_should_write_the_sorted_schema_of_the_app(self, tmp_path: Path) -> None:
        output = tmp_path / "schema.json"

        openapi.export_schema(Path.cwd(), output)

        schema = json.loads(output.read_text())
        assert {"/health", "/ready", "/workspaces"} <= set(schema["paths"])
        assert list(schema) == sorted(schema)

    def test_should_export_through_the_command_line(self, tmp_path: Path) -> None:
        output = tmp_path / "schema.json"

        assert openapi.main(["export", "--output", str(output)]) == 0
        assert "/health" in json.loads(output.read_text())["paths"]


class TestCommands:
    def test_should_return_the_output_of_a_successful_command(self, tmp_path: Path) -> None:
        command = [which("bash"), "-c", "echo out"]

        assert openapi.run_or_fail(command, cwd=tmp_path, timeout=10) == "out\n"

    def test_should_raise_with_the_output_when_the_command_fails(self, tmp_path: Path) -> None:
        command = [which("bash"), "-c", "echo out; echo err >&2; exit 3"]

        with pytest.raises(OpenApiDiffError, match="failed:\nout\nerr"):
            openapi.run_or_fail(command, cwd=tmp_path, timeout=10)

    def test_should_resolve_executables_to_absolute_paths(self) -> None:
        assert Path(openapi.executable("git")).is_absolute()

    def test_should_fail_when_an_executable_is_missing(self) -> None:
        with pytest.raises(OpenApiDiffError, match="not-a-real-tool not found"):
            openapi.executable("not-a-real-tool")

    def test_should_hint_at_the_history_when_the_merge_base_is_missing(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch.object(openapi, "run_or_fail", side_effect=OpenApiDiffError("bad object"))

        with pytest.raises(OpenApiDiffError, match=r"fetch-depth: 0"):
            openapi.merge_base("origin/main", REPOSITORY)

    def test_should_not_leak_the_current_virtual_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VIRTUAL_ENV", "/somewhere/.venv")
        monkeypatch.setenv("PATH", "/bin")

        environment = openapi.export_environment()

        assert "VIRTUAL_ENV" not in environment
        assert environment["PATH"] == "/bin"


class TestExportIn:
    @pytest.fixture
    def sut(self, mocker: MockerFixture) -> MagicMock:
        mocker.patch("scripts.openapi.shutil.which", side_effect=which)
        return mocker.patch.object(openapi, "run_or_fail", return_value="")

    def test_should_export_with_the_checkout_environment_from_outside_the_checkout(
        self, sut: MagicMock, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("VIRTUAL_ENV", "/somewhere/.venv")
        output = tmp_path / openapi.HEAD_SCHEMA

        openapi.export_in(REPOSITORY, output)

        command = sut.call_args.args[0]
        assert command[:3] == [which("uv"), "run", "--project"]
        assert command[3] == str(REPOSITORY)
        assert {"--locked", "--no-dev", "--inexact"} <= set(command)
        assert command[command.index("python") + 1] == str(openapi.SCRIPT)
        assert command[-4:] == ["--app-dir", str(REPOSITORY), "--output", str(output)]
        assert sut.call_args.kwargs["cwd"] == tmp_path
        assert "VIRTUAL_ENV" not in sut.call_args.kwargs["env"]


class TestDiff:
    @pytest.fixture
    def commands(self, mocker: MockerFixture) -> MagicMock:
        mocker.patch("scripts.openapi.shutil.which", side_effect=which)
        return mocker.patch.object(openapi, "run_or_fail", return_value=f"{COMMIT}\n")

    @pytest.fixture
    def oasdiff(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(openapi, "run", return_value=completed(1, "4 changes: 1 error"))

    def issued(self, commands: MagicMock) -> list[list[str]]:
        return [call.args[0] for call in commands.call_args_list]

    def test_should_compare_head_with_the_merge_base_and_keep_the_oasdiff_exit_code(
        self, commands: MagicMock, oasdiff: MagicMock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = openapi.diff_command("origin/main", "oasdiff", REPOSITORY)

        issued = self.issued(commands)
        assert code == 1
        assert issued[0] == [which("git"), "merge-base", "origin/main", "HEAD"]
        assert issued[1][-2] == "--output"
        assert issued[1][issued[1].index("--app-dir") + 1] == str(REPOSITORY)
        assert issued[1][-1].endswith(openapi.HEAD_SCHEMA)
        assert issued[2][:4] == [which("git"), "worktree", "add", "--detach"]
        assert issued[2][-1] == COMMIT
        tree = issued[2][-2]
        assert issued[3][issued[3].index("--app-dir") + 1] == tree
        assert issued[3][-1].endswith(openapi.BASE_SCHEMA)
        assert issued[4] == [which("git"), "worktree", "remove", "--force", tree]
        changelog = oasdiff.call_args.args[0]
        assert changelog[:4] == [
            which("oasdiff"),
            "changelog",
            openapi.BASE_SCHEMA,
            openapi.HEAD_SCHEMA,
        ]
        assert changelog[changelog.index("--fail-on") + 1] == "ERR"
        assert "--allow-external-refs=false" in changelog
        assert "4 changes: 1 error" in capsys.readouterr().out

    def test_should_remove_the_worktree_when_the_base_export_fails(
        self, commands: MagicMock, oasdiff: MagicMock
    ) -> None:
        commands.side_effect = [f"{COMMIT}\n", "", "", OpenApiDiffError("base broke"), ""]

        with pytest.raises(OpenApiDiffError, match="base broke"):
            openapi.diff_command("origin/main", "oasdiff", REPOSITORY)

        assert self.issued(commands)[-1][1:3] == ["worktree", "remove"]
        oasdiff.assert_not_called()

    def test_should_fail_fast_when_oasdiff_is_not_installed(
        self, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        mocker.patch("scripts.openapi.shutil.which", return_value=None)
        commands = mocker.patch.object(openapi, "run_or_fail")

        assert openapi.diff_command("origin/main", "oasdiff", REPOSITORY) == 127
        assert "oasdiff not found" in caplog.text
        commands.assert_not_called()

    @pytest.mark.parametrize(
        "error",
        [OpenApiDiffError("no base"), subprocess.TimeoutExpired(["uv"], 600)],
    )
    def test_should_log_diff_errors_and_exit_with_one(
        self, mocker: MockerFixture, caplog: pytest.LogCaptureFixture, error: Exception
    ) -> None:
        mocker.patch.object(openapi, "diff_command", side_effect=error)

        assert openapi.main(["diff", "--base", "origin/x"]) == 1
        assert str(error) in caplog.text
