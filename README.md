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
| `make test-mcp` | Run the MCP server tests and type check |
| `make hooks` | Run all quality checks (ruff, mypy, bandit, vulture, xenon, pip-audit) |
| `make format-code` | Fix lint issues and format the code |
| `make migrate` | Apply database migrations (requires running DB) |
| `make migration msg="desc"` | Generate a new Alembic migration |

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | - | Host port for `make dev` |
| `APP_NAME` | `Drawdoro` | Product name used by the API (OpenAPI title, messages) and the MCP server; `make dev` also passes it to the frontend as `VITE_APP_NAME`. See [White-label](#white-label) |
| `APP_SLUG` | `drawdoro` | `make dev` only: prefix of the container names and local Postgres user/password/database |
| `ENV` | `development` | `development`, `test` or `production`. Production logs JSON. |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CORS_ORIGINS` | `[]` | JSON list of allowed origins |
| `DATABASE_URL` | `postgresql+asyncpg://drawdoro:drawdoro@localhost:5432/drawdoro` | PostgreSQL async connection URL |
| `VITE_APP_NAME` | `Drawdoro` | Frontend: product name shown in the UI and the page title |
| `VITE_APP_SLUG` | slug of `VITE_APP_NAME` | Frontend: prefix of the browser storage keys (`<slug>:session`, `<slug>:theme`...). Changing it signs everyone out |
| `VITE_API_URL` | `/api` | Frontend base URL for the backend. Defaults to the Vite dev proxy that forwards `/api` to `http://localhost:8000`. |
| `AUTH_ENABLED` | `false` | Require a Cognito sign-in on every API route and WebSocket. Must be `true` when `ENV=production`. |
| `COGNITO_REGION` | `us-east-1` | Region of the Cognito user pool |
| `COGNITO_USER_POOL_ID` | - | User pool whose ID tokens the API accepts |
| `COGNITO_CLIENT_ID` | - | App client id expected in the token audience |
| `SERVICE_API_KEY` | - | Shared secret that lets trusted services (the MCP server) call the API via `X-API-Key` |
| `GALLERY_MAX_IMAGE_BYTES` | `2097152` (2 MiB) | Largest image accepted in the personal gallery (PNG, JPEG, GIF or WebP; stored in Postgres) |
| `GALLERY_MAX_SHAPES_BYTES` | `5242880` (5 MiB) | Largest saved selection (tldraw content JSON, inlined assets included) accepted in the personal gallery |
| `MCP_API_URL` | `http://localhost:8000` | MCP server: backend URL |
| `MCP_API_KEY` | - | MCP server: value sent as `X-API-Key` (same as `SERVICE_API_KEY`) |
| `MCP_FRONTEND_URL` | `http://localhost:3000` | MCP server: frontend whose `/render` page `render_diagram` opens in a headless Chromium |
| `MCP_AGENT_NAME` | `Claude` | MCP server: name shown in the diagram's presence avatars while the agent works on it; empty hides it |
| `MCP_TRANSPORT` | `stdio` | MCP server transport: `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | MCP server bind address when using `streamable-http` |
| `MCP_PORT` | `8001` | MCP server port when using `streamable-http` |
| `MCP_ALLOWED_HOSTS` | - | MCP server: comma-separated hostnames accepted over HTTP besides localhost (the `Host` header; any other gets 421) |
| `VITE_COGNITO_DOMAIN` | - | Frontend: managed login domain; empty disables login |
| `VITE_COGNITO_CLIENT_ID` | - | Frontend: public app client id (no secret) |
| `VITE_COGNITO_IDENTITY_PROVIDER` | `Google` | Frontend: identity provider to skip the Cognito provider picker |

The MCP server still reads the former `DRAWDORO_*` names (`DRAWDORO_API_URL`, `DRAWDORO_MCP_PORT`...) when the
`MCP_*` one is not set, so existing setups keep working. In Kubernetes, a Service named `mcp` would make the kubelet
inject `MCP_PORT=tcp://...`; name the Service otherwise or set `enableServiceLinks: false`.

## White-label

The product name is configuration, not code, so a fork can rebrand the app and still take upstream changes with
`git merge` without conflicts. Code identifiers (classes, shape utils, tldraw ids, the `window.renderDiagram` hook
used by `render_diagram`, package names) are brand-neutral; everything people or agents read comes from:

| Where | Setting | Used for |
|---|---|---|
| API | `APP_NAME` (`app/common/settings.py`) | OpenAPI title, error messages such as "hasn't signed in to <name> yet" |
| MCP server | `APP_NAME` (`mcp/settings.py`) | Server name (slug of the name), description, instructions sent to agents, API error messages |
| Frontend | `VITE_APP_NAME` (`frontend/src/config/branding.ts`) | Page title, logo wordmark, landing, home, 404 and members texts |
| Frontend | `VITE_APP_SLUG` (`frontend/src/config/branding.ts`) | Prefix of the localStorage/sessionStorage keys |
| Docker compose | `APP_NAME`, `APP_SLUG` (root `.env`) | Passes the name to the three services; names the containers and local database |

`VITE_*` variables are read at build time, so set them where the frontend is built (`frontend/.env`, the shell or the
Docker build). For example, a fork called CondoDraw sets `APP_NAME=CondoDraw` for the API and the MCP server and
`VITE_APP_NAME=CondoDraw` for the frontend build; the storage slug then becomes `condodraw`. Deployment files (manifests,
workflows, web server config) and the logo artwork (`frontend/public/favicon.svg`, `components/ui/Logo.tsx`) stay
per fork.

## Authentication

Sign-in uses an Amazon Cognito user pool with Google federation (authorization code + PKCE, no client
secret). The API validates the Cognito **ID token** (`iss`, `aud`, `token_use`, `exp`) on every route
except `/health`, creates the user in `users` on first sign-in, and the WebSocket reads it from `?token=`.
Leave `AUTH_ENABLED=false` and the `VITE_COGNITO_*` variables empty to develop without logging in.

Access is scoped by workspace membership (`workspace_members`): the creator of a workspace becomes its
**owner**, and only members see it. **Viewers** read, **editors** also change content, and **owners** also
manage members and rename or delete the workspace. Resources outside the user's workspaces answer 404.
A workspace always keeps at least one owner. Workspaces that have no members (created before sign-in was
enabled) are adopted by the first signed-in user who lists workspaces.

The app client in the pool needs: no client secret, the *Authorization code grant*, scopes
`openid email profile`, the Google identity provider enabled, callback URL `<app origin>/auth/callback`
and sign-out URL `<app origin>` with no trailing slash (add the `http://localhost:3000` ones for local testing).

Profile photos come from the ID token's `picture` claim: map the Google attribute `picture` to the user pool
attribute `picture` in the Google identity provider and allow the app client to read it. The photo (https
URLs only) is stored on the user, returned by `/me` as `picture_url` and shared in the diagram presence;
without it avatars fall back to the name's initial.

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
    pages/                Landing (sign-in), AuthCallback, Home, Diagram, SharedDiagram, Render (MCP export), NotFound
    auth/                 Cognito managed login: PKCE flow, token storage and refresh
    api/                  Axios client and per-resource API functions
    store/                Zustand stores (app, theme, dialogs, toasts)
    styles/               Design tokens (light/dark) and component styles
    hooks/                Reusable hooks (shortcuts, realtime, comments, presentation)
    utils/                Pure helpers (validation, export, shape selection/connection)
    shapes/               tldraw shape extensions (rounded edges, custom stroke colours)
    config/               White-label branding (product name, storage key prefix)
mcp/                      Python MCP server
  server.py               Entry point: builds the server and registers the tools
  settings.py             Settings read from APP_NAME and MCP_* env vars
  tools/                  MCP tools (diagrams, projects) and the API client
  tests/                  MCP tests (`make test-mcp`)
```

## API routes (placeholder)

| Method | Path | Description |
|---|---|---|
| GET | /me | Signed-in user (creates it on first sign-in), with the profile photo as `picture_url` |
| GET/POST | /workspaces/{id}/members | List members / add a member by email (owner) |
| PUT/DELETE | /workspaces/{id}/members/{user_id} | Change a role (owner) / remove a member (owner, or yourself to leave) |
| GET | /health | Health check |
| GET/POST | /workspaces | List / create workspaces |
| GET/PUT/DELETE | /workspaces/{id} | Get / update / delete workspace |
| GET/POST | /workspaces/{id}/projects | List / create projects |
| GET/PUT/DELETE | /workspaces/{id}/projects/{id} | Get / update / delete project |
| GET/POST | /projects/{id}/folders | List / create folders |
| GET/PUT/DELETE | /projects/{id}/folders/{id} | Get / update / delete folder |
| GET | /projects/{id}/tree | Folders and diagram summaries of a project in one response (the sidebar tree) |
| GET/POST | /projects/{id}/diagrams | List diagram summaries (no canvas or metadata) / create a diagram |
| GET | /diagrams/{id} | Get a diagram by its id alone, as in the editor link `/diagrams/<id>` (used by the MCP server's `open_link`) |
| GET/PUT/DELETE | /projects/{id}/diagrams/{id} | Get / update / delete diagram. Every saved update is pushed to open editors as `diagram_updated`; editor tabs send `X-Client-Id` so they skip the echo of their own saves |
| GET/PUT | /diagrams/{id}/documentation | Get / update documentation page |
| GET/POST | /diagrams/{id}/comments | List / create comments |
| POST | /diagrams/{id}/share | Generate (or return) the diagram's shareable link token |
| GET | /share/{share_token} | Public: open a shared diagram by token, no sign-in required (used by guests) |
| GET/POST | /gallery | List the signed-in user's gallery items (without payloads) / save a selection (`kind=shapes`, tldraw content) or an image (`kind=image`, base64) with a PNG thumbnail |
| GET/PATCH/DELETE | /gallery/{id} | Get an item with its payload / rename / delete it. Items are private: someone else's item answers 404 |
| WS | /ws/diagrams/{id} | Real-time collaboration: broadcasts canvas updates, cursors, peer count and saved changes (`diagram_updated`, including those made through the API or the MCP server) to everyone connected to the same diagram. An agent that reads or saves the diagram through the MCP server (`X-Agent-Name`, honoured only with the service key when auth is on) is listed in the presence for 60s after its last call. Guests join with `?share=<token>&name=<name>` as read-only viewers |

All routes except `/health` return `501 Not Implemented` until infra is wired.

## Adding a feature

1. Model in `domain/entities/` and contract in `domain/contracts/`
2. Use case in `domain/usecases/<feature>/`
3. Contract implementation in `infra/`
4. Factory in `presentation/factories/` and route in `presentation/fastapi/routes/` (register in `routes/__init__.py`)
5. Unit tests in `tests/unit/` and route tests in `tests/integration/`

## MCP server

The MCP server exposes the app's tools to AI coding agents:

| Area | Tools |
|---|---|
| Navigation | `list_workspaces`, `list_projects`, `get_project`, `list_folders`, `list_diagrams` (ids and names only, no canvas) |
| Diagrams | `open_link` (editor `/diagrams/<id>` or read-only `/share/<token>` links), `get_diagram`, `get_diagram_outline`, `create_diagram`, `update_diagram`, `edit_shapes`, `render_diagram` |
| Organisation | `create_project`, `create_folder` |
| Documentation and comments | `get_documentation`, `update_documentation`, `list_comments` |

Nothing deletes workspaces, projects, folders or diagrams (`edit_shapes` only deletes shapes inside a canvas), and
nothing manages members. On connect the server sends instructions telling the agent to call `open_link` when it sees
a link to the app (named after `APP_NAME`), and to prefer the compact tools below over whole canvases.

Configure the backend URL with `MCP_API_URL` (default: `http://localhost:8000`). When the API has `AUTH_ENABLED=true`, set `MCP_API_KEY` to the API's `SERVICE_API_KEY`.

`update_diagram` only changes the fields you pass; the others keep their current values. A canvas is tens of KB of
tldraw JSON, so agents mostly use three tools that avoid moving it around:

- `get_diagram_outline`: every shape with its position, size, colour and plain text, in reading order.
- `edit_shapes`: creates, changes (JSON Merge Patch) or deletes only the given records, with an optional
  `expected_updated_at` guard against overwriting someone else's save. Deleting a shape also deletes its children and
  arrow bindings.
- `render_diagram`: a PNG of the whole canvas, some shapes or a region. The MCP server opens the frontend's `/render`
  page (`MCP_FRONTEND_URL`) in a headless Chromium, so the image matches the editor exactly. Locally, install the
  browser once with `cd mcp && uv run playwright install --only-shell chromium` and keep the frontend running.

While the agent reads or saves a diagram, people with it open see it in the presence avatars (as `MCP_AGENT_NAME`, default `Claude`) until 60s after its last call.

Locally it runs over stdio, so the MCP client starts it. For example, with Claude Code:

```sh
claude mcp add drawdoro -e MCP_API_URL=http://localhost:8000 -- uv run --directory mcp python server.py
```

`make dev` also starts it over HTTP at `http://localhost:8001/mcp` (`MCP_TRANSPORT=streamable-http`). The port is bound to localhost only, because the server holds the service API key and has no auth of its own.
Over HTTP the server is stateless and answers `GET /health`; to serve it behind a proxy, list the public hostname in
`MCP_ALLOWED_HOSTS`.

```sh
claude mcp add --transport http drawdoro http://localhost:8001/mcp
```
