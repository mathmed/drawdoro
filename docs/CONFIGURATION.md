# Configuration

Every setting comes from environment variables. The backend reads them in `app/common/settings.py`, the MCP
server in `mcp/settings.py` and the frontend from its `VITE_*` build variables. Copy `.env.example` to `.env`
to start (`make setup` does it for you). A new variable goes into `app/common/settings.py`, `.env.example`
and the table below.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | - | Host port for `make dev` |
| `APP_NAME` | `Drawdoro` | Product name used by the API (OpenAPI title, messages) and the MCP server; `make dev` also passes it to the frontend as `VITE_APP_NAME`. See [White-label](WHITE_LABEL.md) |
| `APP_SLUG` | `drawdoro` | `make dev` only: prefix of the container names and local Postgres user/password/database |
| `ENV` | `development` | `development`, `test` or `production`. Production logs JSON. |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CORS_ORIGINS` | `[]` | JSON list of allowed origins |
| `DATABASE_URL` | `postgresql+asyncpg://drawdoro:drawdoro@localhost:5432/drawdoro` | PostgreSQL async connection URL |
| `VITE_APP_NAME` | `Drawdoro` | Frontend: product name shown in the UI and the page title |
| `VITE_APP_SLUG` | slug of `VITE_APP_NAME` | Frontend: prefix of the browser storage keys (`<slug>:session`, `<slug>:theme`...). Changing it signs everyone out |
| `VITE_API_URL` | `/api` | Frontend base URL for the backend. Defaults to the Vite dev proxy that forwards `/api` to `http://localhost:8000`. |
| `AUTH_ENABLED` | `false` | Require a Cognito sign-in on every API route and WebSocket. Must be `true` when `ENV=production`. See [Authentication](AUTHENTICATION.md) |
| `COGNITO_REGION` | `us-east-1` | Region of the Cognito user pool |
| `COGNITO_USER_POOL_ID` | - | User pool whose ID tokens the API accepts |
| `COGNITO_CLIENT_ID` | - | App client id expected in the token audience |
| `SERVICE_API_KEY` | - | Shared secret that lets trusted services (the MCP server) call the API via `X-API-Key`, as an agent without owner. People can also create personal keys (see [Diagram history and personal API keys](FEATURES.md#diagram-history-and-personal-api-keys)) |
| `GALLERY_MAX_IMAGE_BYTES` | `2097152` (2 MiB) | Largest image accepted in the personal gallery (PNG, JPEG, GIF or WebP; stored in Postgres) |
| `GALLERY_MAX_SHAPES_BYTES` | `5242880` (5 MiB) | Largest saved selection (tldraw content JSON, inlined assets included) accepted in the personal gallery |
| `GALLERY_MAX_CANVAS_BYTES` | `20971520` (20 MiB) | Largest canvas a diagram may reach when a gallery item is inserted into it (by the API or the MCP server); inserted images are embedded in the canvas |
| `REVISION_INTERVAL_MINUTES` | `10` | Diagram history: a person's saves within this many minutes share one revision (agent changes and restores always get their own) |
| `REVISION_RETENTION_DAYS` | `30` | Diagram history: revisions last updated longer ago are deleted; `0` keeps them regardless of age. The newest one is always kept |
| `REVISION_MAX_PER_DIAGRAM` | `100` | Diagram history: at most this many revisions are kept per diagram, newest first; `0` keeps any number |
| `MCP_API_URL` | `http://localhost:8000` | MCP server: backend URL |
| `MCP_API_KEY` | - | MCP server: value sent as `X-API-Key`: the API's `SERVICE_API_KEY` (agent without owner) or a personal key. Over HTTP, a key sent by the MCP client takes precedence |
| `MCP_FRONTEND_URL` | `http://localhost:3000` | MCP server: frontend whose `/render` page `render_diagram` opens in a headless Chromium |
| `MCP_AGENT_NAME` | `Claude` | MCP server: name shown in the diagram's presence avatars while the agent works on it; empty hides it |
| `MCP_TRANSPORT` | `stdio` | MCP server transport: `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | MCP server bind address when using `streamable-http` |
| `MCP_PORT` | `8001` | MCP server port when using `streamable-http` |
| `MCP_ALLOWED_HOSTS` | - | MCP server: comma-separated hostnames accepted over HTTP besides localhost (the `Host` header; any other gets 421) |
| `VITE_COGNITO_DOMAIN` | - | Frontend: managed login domain; empty disables login |
| `VITE_COGNITO_CLIENT_ID` | - | Frontend: public app client id (no secret) |
| `VITE_COGNITO_IDENTITY_PROVIDER` | `Google` | Frontend: identity provider to skip the Cognito provider picker |
| `VITE_MCP_URL` | `http://localhost:8001/mcp` | Frontend: MCP server URL shown in the *Connect Claude* guide |

`VITE_*` variables are read at build time, so set them where the frontend is built (`frontend/.env`, the shell
or the Docker build).

The MCP server still reads the former `DRAWDORO_*` names (`DRAWDORO_API_URL`, `DRAWDORO_MCP_PORT`...) when the
`MCP_*` one is not set, so existing setups keep working. In Kubernetes, a Service named `mcp` would make the kubelet
inject `MCP_PORT=tcp://...`; name the Service otherwise or set `enableServiceLinks: false`.

The variables of the boot smoke (`SMOKE_*`) are in [Development](DEVELOPMENT.md#boot-smoke).
