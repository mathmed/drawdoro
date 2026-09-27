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
| Diagrams | Mermaid |
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
    enums/                StrEnum types (AdrStatus, WorkspaceRole)
    errors/               Domain errors (NotFoundError, ConflictError...)
    usecases/             One use case per operation
  infra/                  Contract implementations: database, HTTP clients...
  presentation/
    factories/            Build use cases injecting their infra dependencies
    fastapi/              App config, routes, middlewares and error handlers
  main/                   Entry point
frontend/                 React + Vite + TypeScript
  src/
    components/layout/    Sidebar + canvas shell and tabbed right panel (Docs/ADRs/Info)
    components/canvas/    tldraw wrapper with backend persistence and comment context menu
    components/sidebar/   Workspace, project, folder and diagram navigation
    components/docs/      Markdown documentation panel (auto-save)
    components/code/      Mermaid/D2 code panel with live preview (auto-save)
    components/templates/ Built-in diagram template picker modal
    components/comments/  Element-anchored comments panel and canvas badges
    components/adr/        ADR list/form panel with colored status
    components/presentation/ Fullscreen presentation mode navigating frames
    components/semantic/  Shape metadata panel and architecture validation modal
    components/toolbar/   Docs/Code/Templates/Comments/Validate/Present toggles, export and rename
    pages/                Home, Diagram, NotFound
    api/                  Axios client and per-resource API functions
    store/                Zustand global state
    data/                 Static data (built-in templates)
    hooks/                Reusable hooks (useDebounce, useComments, usePresentation)
    utils/                Pure helpers (architecture validation)
    shapes/               Custom tldraw shapes
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
| GET/POST | /templates | List / create templates |
| GET/PUT/DELETE | /templates/{id} | Get / update / delete template |
| GET/POST | /diagrams/{id}/adrs | List / create ADRs |
| GET/PUT/DELETE | /diagrams/{id}/adrs/{id} | Get / update / delete ADR |
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
