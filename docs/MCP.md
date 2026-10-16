# MCP server

The MCP server (`mcp/`, Python MCP SDK) exposes the app's tools to AI coding agents. It calls the backend API,
so the API's permissions are the real limits of what an agent can do. Its settings (`MCP_*`) are in
[Configuration](CONFIGURATION.md).

## Tools

| Area | Tools |
|---|---|
| Navigation | `list_workspaces`, `list_projects`, `get_project`, `list_folders`, `list_diagrams` (ids and names only, no canvas) |
| Diagrams | `open_link` (editor `/diagrams/<id>` or read-only `/share/<token>` links), `get_diagram`, `get_diagram_outline`, `create_diagram`, `update_diagram`, `edit_shapes`, `render_diagram` |
| History | `list_revisions`, `restore_revision` |
| Organisation | `create_project`, `create_folder` |
| Documentation and comments | `get_documentation`, `update_documentation`, `list_comments`, `add_comment`, `resolve_comment`, `reopen_comment`, `delete_comment` |
| Personal gallery | `list_gallery_items`, `get_gallery_item`, `insert_gallery_item`, `update_gallery_item` (a personal key when auth is on) |

Nothing deletes workspaces, projects, folders or diagrams (`edit_shapes` only deletes shapes inside a canvas, and
`delete_comment` only the comments the agent's own key wrote), and nothing manages members. On connect the server
sends instructions telling the agent to call `open_link` when it sees a link to the app (named after `APP_NAME`),
and to prefer the compact tools below over whole canvases.

## Running it

Configure the backend URL with `MCP_API_URL` (default: `http://localhost:8000`). When the API has
`AUTH_ENABLED=true`, set `MCP_API_KEY` to the API's `SERVICE_API_KEY`, or to a personal key so the agent acts as
you (see [Diagram history and personal API keys](FEATURES.md#diagram-history-and-personal-api-keys)).

Locally it runs over stdio, so the MCP client starts it. For example, with Claude Code:

```sh
claude mcp add drawdoro -e MCP_API_URL=http://localhost:8000 -- uv run --directory mcp python server.py
```

`make dev` also starts it over HTTP at `http://localhost:8001/mcp` (`MCP_TRANSPORT=streamable-http`). The port is
bound to localhost only, because the server holds the service API key and has no auth of its own.
Over HTTP the server is stateless and answers `GET /health`; to serve it behind a proxy, list the public hostname in
`MCP_ALLOWED_HOSTS`.

```sh
claude mcp add --transport http drawdoro http://localhost:8001/mcp
```

Over HTTP, the key sent by the MCP client in `X-API-Key` (or `Authorization: Bearer`) is used instead of
`MCP_API_KEY`, so one shared MCP server serves everyone under their own name. The frontend's *Connect Claude*
dialog generates the key and the ready-to-paste commands:

```sh
claude mcp add --transport http drawdoro http://localhost:8001/mcp --header "X-API-Key: mcpk_..."
```

While the agent reads or saves a diagram, people with it open see it in the presence avatars (as
`MCP_AGENT_NAME`, default `Claude`) until 60s after its last call.

## Working with canvases

`update_diagram` and `edit_shapes` take an optional `summary` shown in the diagram's history (a generic one is made
up when it's missing). `update_diagram` only changes the fields you pass; the others keep their current values. A
canvas is tens of KB of tldraw JSON, so agents mostly use three tools that avoid moving it around:

- `get_diagram_outline`: every shape with its position, size, colour and plain text, in reading order.
- `edit_shapes`: creates, changes (JSON Merge Patch) or deletes only the given records, with an optional
  `expected_updated_at` guard against overwriting someone else's save. Deleting a shape also deletes its children and
  arrow bindings.
- `render_diagram`: a PNG of the whole canvas, some shapes or a region. The MCP server opens the frontend's `/render`
  page (`MCP_FRONTEND_URL`) in a headless Chromium, so the image matches the editor exactly. Locally, install the
  browser once with `cd mcp && uv run playwright install --only-shell chromium` and keep the frontend running.

## Comments

Comments are how people ask the agent for changes: `list_comments` (`status="open"` for the pending ones) returns
each comment's id, author (person or agent, with the person it works for), anchored `element_id`, status, who
resolved it and when, and `created_by_you`. The agent answers with `add_comment` and closes what it addressed with
`resolve_comment` (anyone's comment, reversible with `reopen_comment`); `delete_comment` is refused for anything its
key didn't write. The comment text comes in an `untrusted_user_content` field next to a `notice` saying it is data,
not instructions, and the tool descriptions and server instructions say the same. That lowers the risk of prompt
injection through comments but can't rule it out: the real limits are the backend permissions
([Comments](FEATURES.md#comments)).

## Personal gallery

The gallery tools need a personal key when auth is on; how the gallery and insertions behave, and the tools agents
use on it, are in [Personal gallery](FEATURES.md#personal-gallery).

## Available tools

The *Connect Claude* dialog has an *Available tools* tab listing every MCP tool by area, with search, a button to
copy the name and badges for the tools that need a personal key or the editor role. It reads
`frontend/src/config/mcpTools.json`, generated from the server's real tool registry (`mcp/catalog.py` holds each
tool's area and requirements, the docstrings hold the descriptions) by `make mcp-manifest`; `mcp/tests/test_manifest.py`
and a pre-commit hook fail when the file is out of date.

## Tests

`make test-mcp` runs the MCP server tests and type check; `make smoke-mcp` boots it over HTTP (see
[Development](DEVELOPMENT.md#boot-smoke)).
