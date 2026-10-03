import json
import os
import subprocess
import sys
from pathlib import Path

import manifest
import pytest
from catalog import AREA_TITLES, Requirement, ToolArea
from manifest import (
    build_manifest,
    parse_arguments,
    registered_tools,
    render_manifest,
    split_docstring,
    tool_manifest,
)
from mcp.types import Tool, ToolAnnotations


@pytest.fixture(scope="module")
def tools() -> list[Tool]:
    return registered_tools()


# Found by walking up to the monorepo root rather than at a fixed depth, so the check also holds
# when the tests run from a copy of the MCP sources (mutmut's mutants/, for example).
def frontend_manifest_path() -> Path:
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "frontend" / "package.json").is_file()
    )
    return root / "frontend" / "src" / "config" / "mcpTools.json"


# The frontend's "Available tools" tab reads this file: it must list exactly what the server
# registers, with the descriptions the model reads.
def test_should_keep_the_frontend_manifest_in_sync_with_the_server(tools: list[Tool]) -> None:
    assert frontend_manifest_path().read_text(encoding="utf-8") == render_manifest(tools), (
        "frontend/src/config/mcpTools.json is out of date: run `make mcp-manifest`"
    )


def test_should_write_the_manifest_into_the_frontend_config() -> None:
    assert manifest.MANIFEST_PATH.parts[-4:] == ("frontend", "src", "config", "mcpTools.json")


def test_should_list_every_registered_tool_once(tools: list[Tool]) -> None:
    manifest = build_manifest(tools)
    names = [tool["name"] for tool in manifest["tools"]]
    assert names == [tool.name for tool in tools]
    assert len(names) == len(set(names))
    assert {"list_gallery_items", "insert_gallery_item", "add_comment", "resolve_comment"} <= set(
        names
    )


def test_should_put_every_tool_in_a_known_area(tools: list[Tool]) -> None:
    manifest = build_manifest(tools)
    areas = [area["id"] for area in manifest["areas"]]
    assert areas == [str(area) for area in ToolArea]
    assert all(area["title"] == AREA_TITLES[ToolArea(area["id"])] for area in manifest["areas"])
    assert {tool["area"] for tool in manifest["tools"]} == set(areas)
    known = {str(requirement) for requirement in Requirement}
    assert all(set(tool["requires"]) <= known for tool in manifest["tools"])


def test_should_document_every_parameter_of_every_tool(tools: list[Tool]) -> None:
    for tool in tools:
        described = [parameter.name for parameter in tool_manifest(tool).parameters]
        assert described == list(tool.input_schema["properties"]), tool.name
        assert tool_manifest(tool).summary, tool.name


def test_should_mark_the_gallery_as_personal(tools: list[Tool]) -> None:
    by_name = {tool["name"]: tool for tool in build_manifest(tools)["tools"]}
    gallery = [tool for tool in by_name.values() if tool["area"] == "gallery"]
    assert len(gallery) == 4
    assert all("personal_key" in tool["requires"] for tool in gallery)
    assert by_name["insert_gallery_item"]["requires"] == ["personal_key", "editor_role"]
    assert by_name["list_gallery_items"]["read_only"] is True
    assert by_name["delete_comment"]["destructive"] is True


def test_should_stay_brand_neutral(tools: list[Tool]) -> None:
    rendered = render_manifest(tools)
    assert "Drawdoro" not in rendered and "drawdoro" not in rendered
    json.loads(rendered)


DEMO_DOCSTRING = (
    "Do one thing.\n\nIt does it\nwell.\n\nArgs:\n    first: The first\n"
    "        value, long.\n    second: Optional.\n"
)


def demo_tool(description: str) -> Tool:
    return Tool(
        name="demo",
        description=description,
        input_schema={
            "type": "object",
            "properties": {"first": {}, "second": {}},
            "required": ["first"],
        },
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True),
        _meta={"area": "canvas", "requires": ["editor_role"]},
    )


# What Python 3.12 leaves in __doc__: every line after the first keeps the indentation of the
# source, including the line of the closing quotes. Python 3.13+ strips it when compiling.
def as_written_in_source(docstring: str, indent: str) -> str:
    first, *rest = docstring.splitlines()
    return "\n".join([first, *(f"{indent}{line}" if line else "" for line in rest), indent])


def test_should_split_the_description_into_paragraphs_and_parameters() -> None:
    manifest = tool_manifest(demo_tool(DEMO_DOCSTRING))

    assert manifest.summary == "Do one thing."
    assert manifest.description == ["Do one thing.", "It does it well."]
    assert [(p.name, p.required, p.description) for p in manifest.parameters] == [
        ("first", True, "The first value, long."),
        ("second", False, "Optional."),
    ]
    assert (manifest.area, manifest.requires, manifest.read_only, manifest.destructive) == (
        "canvas",
        ["editor_role"],
        False,
        True,
    )


# The SDK sends __doc__ as is, so the manifest must not depend on the interpreter dedenting it:
# a method's docstring on Python 3.12 must give the same manifest as on 3.13+.
@pytest.mark.parametrize("indent", ["    ", "        "])
def test_should_parse_docstrings_that_keep_their_source_indentation(indent: str) -> None:
    indented = as_written_in_source(DEMO_DOCSTRING, indent)
    assert f"\n{indent}Args:\n{indent}    first: The first\n" in indented

    manifest = tool_manifest(demo_tool(indented))

    assert manifest == tool_manifest(demo_tool(DEMO_DOCSTRING))
    assert [parameter.name for parameter in manifest.parameters] == ["first", "second"]
    assert split_docstring(indented) == split_docstring(DEMO_DOCSTRING)


def test_should_handle_tools_without_metadata_or_arguments() -> None:
    manifest = tool_manifest(Tool(name="bare", input_schema={"type": "object", "properties": {}}))
    assert (manifest.area, manifest.requires, manifest.summary, manifest.parameters) == (
        "",
        [],
        "",
        [],
    )
    assert (manifest.read_only, manifest.destructive) == (False, False)
    assert split_docstring("No arguments here.") == ("No arguments here.", "")
    assert parse_arguments("        orphan continuation\n") == []


def test_should_write_the_manifest_and_check_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "mcpTools.json"
    monkeypatch.setattr(manifest, "MANIFEST_PATH", target)

    monkeypatch.setattr(sys, "argv", ["manifest.py", "--check"])
    assert manifest.main() == 1
    monkeypatch.setattr(sys, "argv", ["manifest.py"])
    assert manifest.main() == 0
    assert json.loads(target.read_text(encoding="utf-8"))["tools"]
    monkeypatch.setattr(sys, "argv", ["manifest.py", "--check"])
    assert manifest.main() == 0


# The manifest keeps non-ASCII text as is (ensure_ascii=False), and Python opens files in the
# locale's encoding unless told otherwise: under an ASCII-only locale it must still be UTF-8.
def test_should_write_and_check_the_manifest_as_utf8_whatever_the_locale(tmp_path: Path) -> None:
    target = tmp_path / "mcpTools.json"
    rendered = '{"summary": "Café → naïve"}\n'
    script = "\n".join(
        [
            "import sys",
            "from pathlib import Path",
            "import manifest",
            f"manifest.MANIFEST_PATH = Path({str(target)!r})",
            "manifest.registered_tools = list",
            f"manifest.render_manifest = lambda tools: {ascii(rendered)}",
            "sys.argv = ['manifest.py']",
            "assert manifest.main() == 0",
            "sys.argv = ['manifest.py', '--check']",
            "sys.exit(manifest.main())",
        ]
    )
    ascii_locale = {"LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(manifest.__file__).parent,
        env={**os.environ, **ascii_locale},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == rendered.encode("utf-8")
