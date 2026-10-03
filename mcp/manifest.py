import argparse
import asyncio
import inspect
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from catalog import AREA_TITLES
from mcp.types import Tool, ToolAnnotations
from server import create_api, create_server
from settings import Settings
from tools.api import JsonObject
from tools.render import RenderRequest

# The frontend lists the available tools from this file ("Available tools" in Connect Claude).
# It is generated from the tools the server registers, so it can't drift from what agents get:
# `make mcp-manifest` rewrites it and tests/test_manifest.py fails when it is out of date.
MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "frontend" / "src" / "config" / "mcpTools.json"
)
ARGS_HEADER = re.compile(r"^Args:\s*$", re.MULTILINE)
ARGUMENT = re.compile(r"^ {4}(?P<name>\w+): (?P<text>.*)$")
CONTINUATION = re.compile(r"^ {8}(?P<text>\S.*)$")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Parameter:
    name: str
    required: bool
    description: str


@dataclass(frozen=True)
class ToolManifest:
    name: str
    area: str
    requires: list[str]
    read_only: bool
    destructive: bool
    # The first paragraph of the description, for lists.
    summary: str
    # The description the model reads, without the Args section, one string per paragraph.
    description: list[str]
    parameters: list[Parameter]


class NoRenderer:
    def render(self, canvas_state: JsonObject, request: RenderRequest) -> bytes:
        raise NotImplementedError("The manifest only lists the tools")


def registered_tools() -> list[Tool]:
    settings = Settings()
    server = create_server(settings, create_api(settings), NoRenderer())
    return asyncio.run(server.list_tools())


def build_manifest(tools: list[Tool]) -> dict[str, Any]:
    return {
        "areas": [{"id": str(area), "title": title} for area, title in AREA_TITLES.items()],
        "tools": [asdict(tool_manifest(tool)) for tool in tools],
    }


def render_manifest(tools: list[Tool]) -> str:
    return json.dumps(build_manifest(tools), indent=2, ensure_ascii=False) + "\n"


def tool_manifest(tool: Tool) -> ToolManifest:
    meta = tool.meta or {}
    body, arguments = split_docstring(tool.description or "")
    paragraphs = docstring_paragraphs(body)
    return ToolManifest(
        name=tool.name,
        area=str(meta.get("area", "")),
        requires=[str(requirement) for requirement in meta.get("requires", [])],
        read_only=is_read_only(tool.annotations),
        destructive=is_destructive(tool.annotations),
        summary=next(iter(paragraphs), ""),
        description=paragraphs,
        parameters=tool_parameters(tool, arguments),
    )


def docstring_paragraphs(body: str) -> list[str]:
    paragraphs = [
        " ".join(line.strip() for line in part.splitlines()) for part in body.split("\n\n")
    ]
    return [paragraph for paragraph in paragraphs if paragraph]


def is_read_only(annotations: ToolAnnotations | None) -> bool:
    return bool(annotations and annotations.read_only_hint)


def is_destructive(annotations: ToolAnnotations | None) -> bool:
    return bool(annotations and annotations.destructive_hint)


def tool_parameters(tool: Tool, arguments: str) -> list[Parameter]:
    required = set(tool.input_schema.get("required", []))
    return [
        Parameter(name=name, required=name in required, description=text)
        for name, text in parse_arguments(arguments)
    ]


# The SDK sends __doc__ as is, and only Python 3.13+ strips the source indentation from it when
# compiling: normalise it first so the manifest is the same on every interpreter.
def split_docstring(description: str) -> tuple[str, str]:
    parts = ARGS_HEADER.split(inspect.cleandoc(description), maxsplit=1)
    return parts[0].strip(), parts[1] if len(parts) > 1 else ""


def parse_arguments(section: str) -> list[tuple[str, str]]:
    arguments: list[tuple[str, str]] = []
    for line in section.splitlines():
        if match := ARGUMENT.match(line):
            arguments.append((match["name"], match["text"].strip()))
        elif (match := CONTINUATION.match(line)) and arguments:
            name, text = arguments[-1]
            arguments[-1] = (name, f"{text} {match['text'].strip()}")
    return arguments


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Write the frontend's list of MCP tools")
    parser.add_argument("--check", action="store_true", help="fail if the file is out of date")
    args = parser.parse_args()
    rendered = render_manifest(registered_tools())
    current = MANIFEST_PATH.read_text(encoding="utf-8") if MANIFEST_PATH.exists() else ""
    if args.check:
        if current != rendered:
            logger.error("%s is out of date: run `make mcp-manifest`", MANIFEST_PATH)
            return 1
        logger.info("%s is up to date", MANIFEST_PATH)
        return 0
    MANIFEST_PATH.write_text(rendered, encoding="utf-8")
    logger.info("wrote %s", MANIFEST_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
