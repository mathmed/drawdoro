# Architecture

Drawdoro is a monorepo with three parts: a FastAPI backend (this repository's root), a React frontend in
`frontend/` and a Python MCP server in `mcp/`. The backend follows a layered (clean) architecture whose
dependencies point inward, to the domain; `make lint-imports` fails on an import that breaks the
[contracts](#architecture-contracts). [`CLAUDE.md`](../CLAUDE.md) holds the full rules people and AI agents
follow.

## Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python 3.14 |
| Frontend | React 18 + Vite + TypeScript |
| Canvas | tldraw |
| State | Zustand |
| Docs | @uiw/react-md-editor |
| Icons | lucide-react |
| HTTP client | Axios |
| MCP server | Python MCP SDK |

## Folder structure

```
app/
  common/                 Cross-cutting: settings and logging
  domain/                 Business core, framework-free
    contracts/            Interfaces implemented by infra (repositories, gateways)
    entities/             Models and value objects
    enums/                StrEnum types (WorkspaceRole)
    errors/               Domain errors (NotFoundError, ConflictError...)
    usecases/             One use case per operation
  infra/                  Contract implementations: database, HTTP clients...
  presentation/
    factories/            Build use cases injecting their infra dependencies
    fastapi/              App config, routes, middlewares and error handlers
  main/                   Entry point
frontend/                 React + Vite + TypeScript
  src/
    components/layout/    App shell and tabbed right panel (Properties/Docs/Comments)
    components/topbar/    Breadcrumbs, inline rename, save status, presence, Validate/Export/Present
    components/sidebar/   Workspace switcher and project/folder/diagram tree with rename/delete and who is in each
    components/home/      Project overview and onboarding screens
    components/canvas/    tldraw wrapper: persistence, style panel, toolbar, quick-connect handles
    components/presence/  Presence avatars and the other people's live cursors on the canvas
    components/palette/   Command palette (Cmd/Ctrl+K)
    components/diagram/   New diagram dialog
    components/docs/      Markdown documentation panel (auto-save)
    components/comments/  Element-anchored comments panel and canvas pins
    components/presentation/ Fullscreen presentation mode navigating frames
    components/semantic/  Shape properties panel and architecture validation modal
    components/ui/        Design-system primitives: modal, menu, dialogs, toasts, empty states
    components/ui/loading/ Loading states: brand loader, overlay, skeletons, spinner, top progress bar
    pages/                Landing (sign-in), AuthCallback, Home, Diagram, SharedDiagram, Render (MCP export), NotFound
    auth/                 Cognito managed login: PKCE flow, token storage and refresh
    api/                  Axios client and per-resource API functions
    store/                Zustand stores (app, theme, dialogs, toasts, workspace presence)
    styles/               Design tokens (light/dark) and component styles
    hooks/                Reusable hooks (shortcuts, realtime, workspace presence, cursor broadcast, comments, presentation, delayed loader visibility)
    utils/                Pure helpers (validation, export, shape selection/connection, remote cursors and their throttle, sidebar presence)
    shapes/               tldraw shape extensions (rounded edges, custom stroke colours)
    config/               White-label branding (product name, storage key prefix)
mcp/                      Python MCP server
  server.py               Entry point: builds the server and registers the tools
  settings.py             Settings read from APP_NAME and MCP_* env vars
  tools/                  MCP tools (diagrams, projects) and the API client
  tests/                  MCP tests (`make test-mcp`)
scripts/                  Validation tooling: boot smoke (API and MCP), mutation testing helpers and the CI Quality Report
```

## Domain entities

| Entity | Description |
|---|---|
| Workspace | Group of users; top-level organisational unit |
| Project | Belongs to a Workspace; groups diagrams and folders |
| Folder | Nestable; belongs to a Project or another Folder |
| Diagram | canvas_state (tldraw JSON), semantic_metadata |
| DiagramThumbnail | Preview of a Diagram in one theme (light/dark) for the listing cards, rendered by an editor's browser |
| DocumentationPage | Markdown page linked to a Diagram (one per diagram) |
| Comment | Anchored to a diagram element via element_id |
| CustomShape | tldraw custom shape owned by a user or Workspace |
| GalleryItem | Personal reusable item (tldraw shapes snapshot or image) visible only to its owner |
| User | Member of one or more Workspaces |
| WorkspaceMember | User x Workspace join with role: owner/editor/viewer |

## Architecture contracts

[import-linter](https://import-linter.readthedocs.io/) contracts live in `[tool.importlinter]` of
`pyproject.toml` (API) and `mcp/pyproject.toml` (MCP server) and run in pre-commit and CI
(`make lint-imports`):

- layers `app.main` → `app.presentation` → `app.infra` → `app.domain`;
- inside the domain, `usecases` → `services` → `contracts` → `entities` → `enums | errors | constants`;
- the domain imports neither `app.common` nor frameworks and drivers (FastAPI, Starlette, SQLAlchemy,
  asyncpg, Alembic, httpx, PyJWT, pydantic-settings, uvicorn); `app.common` imports no other layer;
- use case groups and infra adapters are independent of each other;
- infra does not import the web framework, and only factories wire infra into the presentation;
- MCP: tools import neither `server` nor `settings`, tool groups depend on `diagrams` → `canvas` →
  `api`, and only `tools.api` imports httpx.

The contracts hold with **no baseline**: there are no `ignore_imports` entries. A new violation is fixed in
the import (a domain port, a factory) rather than tolerated; adding entries or relaxing a contract needs the
owner's approval.

## Adding a feature

1. Model in `domain/entities/` and contract in `domain/contracts/`
2. Use case in `domain/usecases/<feature>/`
3. Contract implementation in `infra/`
4. Factory in `presentation/factories/` and route in `presentation/fastapi/routes/` (register in `routes/__init__.py`)
5. Unit tests in `tests/unit/` and route tests in `tests/integration/`
