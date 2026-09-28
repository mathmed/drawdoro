# Drawdoro

Internal architecture diagramming and documentation tool. Create, annotate and document software architecture diagrams with real-time collaboration.

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

## Quick start

```sh
make setup     install uv, dependencies and git hooks
make run       start the API at http://localhost:8000
```

Frontend (separate terminal):
```sh
cd frontend
npm install
npm run dev    starts at http://localhost:3000
```

Or run everything with Docker:
```sh
make dev
```

Health check: `curl http://localhost:8000/health`

## Commands

| Command | Description |
|---|---|
| `make setup` | Install uv, project dependencies and git hooks |
| `make run` | Run the API locally with hot reload |
| `make dev` | Run all services with Docker |
| `make db` | Start only the Postgres database with Docker (detached, waits for healthcheck) |
| `make build` | Build the production Docker image |
| `make test` | Run all tests with coverage |
| `make test-unit` | Run only the unit tests |
| `make hooks` | Run all quality checks (ruff, mypy, bandit, vulture, xenon, pip-audit) |
| `make format-code` | Fix lint issues and format the code |
| `make migrate` | Apply database migrations (requires running DB) |
| `make migration msg="desc"` | Generate a new Alembic migration |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | - | Host port for `make dev` |
| `ENV` | `development` | `development`, `test` or `production`. Production logs JSON. |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CORS_ORIGINS` | `[]` | JSON list of allowed origins |
| `DRAWDORO_API_URL` | `http://localhost:8000` | Backend URL used by the MCP server |
| `DATABASE_URL` | `postgresql+asyncpg://drawdoro:drawdoro@localhost:5432/drawdoro` | PostgreSQL async connection URL |
| `VITE_API_URL` | `/api` | Frontend base URL for the backend. Defaults to the Vite dev proxy that forwards `/api` to `http://localhost:8000`. |

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
    components/sidebar/   Workspace switcher and project/folder/diagram tree with rename/delete
    components/home/      Project overview and onboarding screens
    components/canvas/    tldraw wrapper: persistence, style panel, toolbar, quick-connect handles
    components/palette/   Command palette (Cmd/Ctrl+K)
    components/diagram/   New diagram dialog
    components/docs/      Markdown documentation panel (auto-save)
    components/comments/  Element-anchored comments panel and canvas pins
    components/presentation/ Fullscreen presentation mode navigating frames
    components/semantic/  Shape properties panel and architecture validation modal
    components/ui/        Design-system primitives: modal, menu, dialogs, toasts, empty states
    pages/                Home, Diagram, NotFound
    api/                  Axios client and per-resource API functions
    store/                Zustand stores (app, theme, dialogs, toasts)
    styles/               Design tokens (light/dark) and component styles
    hooks/                Reusable hooks (shortcuts, realtime, comments, presentation)
    utils/                Pure helpers (validation, export, shape selection/connection)
    shapes/               tldraw shape extensions (rounded edges, custom stroke colours)
mcp/                      Python MCP server
  server.py               Entry point
  tools/                  MCP tools (diagrams, projects)
```

## API routes (placeholder)

| Method | Path | Description |
|---|---|---|
| GET | /health | Health check |
| GET/POST | /workspaces | List / create workspaces |
| GET/PUT/DELETE | /workspaces/{id} | Get / update / delete workspace |
| GET/POST | /workspaces/{id}/projects | List / create projects |
| GET/PUT/DELETE | /workspaces/{id}/projects/{id} | Get / update / delete project |
| GET/POST | /projects/{id}/folders | List / create folders |
| GET/PUT/DELETE | /projects/{id}/folders/{id} | Get / update / delete folder |
| GET/POST | /projects/{id}/diagrams | List / create diagrams |
| GET/PUT/DELETE | /projects/{id}/diagrams/{id} | Get / update / delete diagram |
| GET/PUT | /diagrams/{id}/documentation | Get / update documentation page |
| GET/POST | /diagrams/{id}/comments | List / create comments |
| WS | /ws/diagrams/{id} | Real-time collaboration: broadcasts canvas updates, cursors and peer count to everyone connected to the same diagram |

All routes except `/health` return `501 Not Implemented` until infra is wired.

## Adding a feature

1. Model in `domain/entities/` and contract in `domain/contracts/`
2. Use case in `domain/usecases/<feature>/`
3. Contract implementation in `infra/`
4. Factory in `presentation/factories/` and route in `presentation/fastapi/routes/` (register in `routes/__init__.py`)
5. Unit tests in `tests/unit/` and route tests in `tests/integration/`

## MCP server

The MCP server exposes Drawdoro tools to AI coding agents. Configure the backend URL with the `DRAWDORO_API_URL` env var (default: `http://localhost:8000`).

```sh
cd mcp
uv run python server.py
```
