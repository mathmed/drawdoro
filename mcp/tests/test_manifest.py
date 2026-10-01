import json
import sys
from pathlib import Path

import manifest
import pytest
from catalog import AREA_TITLES, Requirement, ToolArea
from manifest import (
    MANIFEST_PATH,
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


# The frontend's "Available tools" tab reads this file: it must list exactly what the server
# registers, with the descriptions the model reads.
def test_should_keep_the_frontend_manifest_in_sync_with_the_server(tools: list[Tool]) -> None:
    assert MANIFEST_PATH.read_text() == render_manifest(tools), (
        "frontend/src/config/mcpTools.json is out of date: run `make mcp-manifest`"
    )


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


def test_should_split_the_description_into_paragraphs_and_parameters() -> None:
    tool = Tool(
        name="demo",
        description=(
            "Do one thing.\n\nIt does it\nwell.\n\nArgs:\n    first: The first\n"
            "        value, long.\n    second: Optional.\n"
        ),
        input_schema={
            "type": "object",
            "properties": {"first": {}, "second": {}},
            "required": ["first"],
        },
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True),
        _meta={"area": "canvas", "requires": ["editor_role"]},
    )

    manifest = tool_manifest(tool)

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
    assert json.loads(target.read_text())["tools"]
    monkeypatch.setattr(sys, "argv", ["manifest.py", "--check"])
    assert manifest.main() == 0
