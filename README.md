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

### Frontend checks

The frontend needs Node.js 22 or newer. From `frontend/`:

| Command | Description |
|---|---|
| `npm run lint` | ESLint (`eslint.config.js`): TypeScript, React Hooks and React Refresh rules; fails on any warning (`--max-warnings 0`) |
| `npm run typecheck` | `tsc --noEmit` over `src/`, tests included |
| `npm test` | Vitest + React Testing Library on jsdom, once |
| `npm run test:watch` | Vitest in watch mode |
| `npm run test:coverage` | Tests with V8 coverage; the report goes to `frontend/coverage/` |
| `npm run build` | Type check and production build |

Tests live next to the code as `*.test.ts(x)`; shared helpers are in `src/test/`. They cover the pure and critical
modules (branding, auth session, Zustand stores, formatting and validation utilities), simple components and the loading
states of the main screens; the tldraw canvas is not unit tested. Tests always run with `VITE_APP_NAME=Test App` (set in `vitest.config.ts`), so they never
depend on the product name or on a local `.env`.

Coverage thresholds (`vitest.config.ts`) fail the run when coverage drops: a low global floor (10%; about 40% is covered today, since the
canvas and several views are untested) and stricter per-file floors for the covered modules (90% for the auth session,
branding and utilities; 60% for the stores). Raise them as tests are added.

CI runs the `frontend` job on every pull request and on pushes to `main`: `npm ci`, lint, type check, tests with
coverage and `vite build`.

### Loading states

Every wait uses the primitives in `frontend/src/components/ui/loading/` (CSS in `src/styles/loading.css`, no animation
library):

| Primitive | Use it for |
|---|---|
| `BrandLoader` | Full-area waits (session check, sign-in, opening a diagram or a shared link): the product logo with a soft halo, an orbiting arc and a sheen, a label, and after 8 s a "taking longer than usual" hint with an optional retry |
| `LoadingOverlay` | Covers an area with a loader while the content mounts underneath, then fades out (`screen` for the whole viewport) |
| `LoadingGate` | Swaps content for a fallback (usually a skeleton), with an optional `placeholder` that reserves the room during the delay |
| `Skeleton`, `SkeletonGroup`, `ListSkeleton` | Placeholders with a shimmer that mirror the real layout (sidebar rows, diagram cards, gallery tiles, lists), so nothing moves when the data arrives |
| `Spinner` | Pending buttons and small areas; set `aria-busy` on the busy element |
| `TopProgressBar` | Work that keeps the current content on screen (switching diagrams, refreshing a project) |
| `CanvasLoadingScreen` | tldraw's `LoadingScreen` slot; takes over seamlessly from a loader already on screen |

`useDelayedVisibility` (in `src/hooks/`) drives them: a loader appears only after 180 ms, so fast loads never flash
one, and once shown it stays at least 450 ms, so it never flickers. Loaders announce themselves with `role="status"`,
the decorative blocks are `aria-hidden`, and with `prefers-reduced-motion` every movement becomes a slow fade.

Or run everything with Docker:
```sh
make dev
```

Health checks: `curl http://localhost:8000/health` (liveness, never touches the database) and
`curl http://localhost:8000/ready` (readiness: `503` while the database is unreachable).

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
| `make test-frontend` | Run the frontend lint, type check and tests with coverage |
| `make hooks` | Run all quality checks (ruff, mypy, bandit, vulture, xenon, pip-audit) |
| `make format-code` | Fix lint issues and format the code |
| `make smoke` | Boot smoke: clean Postgres, `alembic upgrade head`, real API (auth on and off), `/health`, `/ready` and the MCP server. See [Validation](#validation-of-agent-generated-code) |
| `make smoke-mcp` | MCP smoke only: streamable-http server, `/health`, `initialize` and `tools/list` |
| `make lint-imports` | Check the architecture contracts (import-linter) of the API and the MCP server |
| `make mutation` | Mutation testing (mutmut) of the use cases and domain services; report in `mutants/report.md` |
| `make mcp-manifest` | Regenerate `frontend/src/config/mcpTools.json` (the *Available tools* list in *Connect Claude*) from the tools the MCP server registers. The MCP tests and a pre-commit hook fail while it is out of date |
| `make mutation-changed` | What the PR job runs: mutation testing of only the use cases and domain services changed against `BASE` (default `origin/main`) |
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
| `SERVICE_API_KEY` | - | Shared secret that lets trusted services (the MCP server) call the API via `X-API-Key`, as an agent without owner. People can also create personal keys (see [Diagram history and personal API keys](#diagram-history-and-personal-api-keys)) |
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
| Frontend | `VITE_APP_NAME` (`frontend/src/config/branding.ts`) | Page title, logo wordmark, loading screens, landing, home, 404 and members texts |
| Frontend | `VITE_APP_SLUG` (`frontend/src/config/branding.ts`) | Prefix of the localStorage/sessionStorage keys |
| Docker compose | `APP_NAME`, `APP_SLUG` (root `.env`) | Passes the name to the three services; names the containers and local database |

`VITE_*` variables are read at build time, so set them where the frontend is built (`frontend/.env`, the shell or the
Docker build). For example, a fork called CondoDraw sets `APP_NAME=CondoDraw` for the API and the MCP server and
`VITE_APP_NAME=CondoDraw` for the frontend build; the storage slug then becomes `condodraw`. Deployment files (manifests,
workflows, web server config) and the logo artwork (`frontend/public/favicon.svg`, `components/ui/Logo.tsx`) stay
per fork.

The loading screens are branded the same way: `BrandLoader` (boot, sign-in, opening a diagram or a shared link) draws
the `Logo` component and, where it shows a name, `branding.name`, so a build with `VITE_APP_NAME=CondoDraw` shows the
CondoDraw name with no code change. To change the logo a fork replaces the artwork in `components/ui/Logo.tsx` (and
`public/favicon.svg`); the loaders, the landing page and the headers all pick it up, since none of them draws the mark
themselves. The loader colours (halo, orbiting arc, progress bar) come from the `--accent` token in
`frontend/src/styles/tokens.css`.

## Authentication

Sign-in uses an Amazon Cognito user pool with Google federation (authorization code + PKCE, no client
secret). The API validates the Cognito **ID token** (`iss`, `aud`, `token_use`, `exp`) on every route
except `/health` and `/ready`, creates the user in `users` on first sign-in, and the WebSocket reads it from `?token=`.
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

## API routes (placeholder)

| Method | Path | Description |
|---|---|---|
| GET | /me | Signed-in user (creates it on first sign-in), with the profile photo as `picture_url` |
| GET/POST | /workspaces/{id}/members | List members / add a member by email (owner) |
| PUT/DELETE | /workspaces/{id}/members/{user_id} | Change a role (owner) / remove a member (owner, or yourself to leave) |
| GET | /health | Liveness: the process answers (`{"status": "ok"}`); never touches the database |
| GET | /ready | Readiness: `{"status": "ready"}` when the database answers, `503` otherwise |
| GET/POST | /workspaces | List / create workspaces |
| GET/PUT/DELETE | /workspaces/{id} | Get / update / delete workspace |
| GET/POST | /workspaces/{id}/projects | List / create projects |
| GET/PUT/DELETE | /workspaces/{id}/projects/{id} | Get / update / delete project |
| GET/POST | /projects/{id}/folders | List / create folders |
| GET/PUT/DELETE | /projects/{id}/folders/{id} | Get / update / delete folder |
| GET | /projects/{id}/tree | Folders and diagram summaries of a project in one response (the sidebar tree) |
| GET/POST | /projects/{id}/diagrams | List diagram summaries (no canvas or metadata) / create a diagram |
| GET | /diagrams/{id} | Get a diagram by its id alone, as in the editor link `/diagrams/<id>` (used by the MCP server's `open_link`) |
| GET | /projects/{id}/diagrams/thumbnails | The previews of the project's diagrams in one theme (`?theme=light`, the default, or `dark`), in one query, for the listing cards: `diagram_id`, `version`, `mime_type` and `image_base64`. Diagrams without a preview are left out. See [Diagram previews](#diagram-previews) |
| PUT | /diagrams/{id}/thumbnail | Store the light and dark previews of a diagram (editor): `version` (the diagram's `updated_at` they were rendered from), `light_base64` and `dark_base64` (PNG or WebP, up to 64 KiB each; `null` when there is nothing to show). An older version never replaces a newer one. `204` |
| GET/PUT/DELETE | /projects/{id}/diagrams/{id} | Get / update / delete diagram. Every saved update is pushed to open editors as `diagram_updated`; editor tabs send `X-Client-Id` so they skip the echo of their own saves |
| GET/PUT | /diagrams/{id}/documentation | Get / update documentation page |
| GET/POST | /diagrams/{id}/comments | List comments (`?status=open`, `resolved` or `all`, the default) / create one (editor). Plain text up to 5000 characters; `element_id` is optional (omitted for a comment on the whole diagram) |
| PATCH/DELETE | /diagrams/{id}/comments/{comment_id} | Resolve or reopen (`{"resolved": true}`) / delete a comment (editor). Agents only delete the comments their own key wrote; see [Comments](#comments) |
| POST | /diagrams/{id}/share | Generate (or return) the diagram's shareable link token |
| GET | /diagrams/{id}/revisions | Diagram history, newest first, without snapshots (`?limit=`, up to 200) |
| GET | /diagrams/{id}/revisions/{revision_id} | One revision with its snapshot (name, canvas and shape metadata) |
| POST | /diagrams/{id}/revisions/{revision_id}/restore | Bring the canvas and shape metadata of a revision back (editor). Recorded as a new revision and pushed to open editors |
| GET/POST | /me/api-keys | List / create the signed-in user's personal API keys. The secret is only in the creation response |
| DELETE | /me/api-keys/{key_id} | Revoke a personal API key |
| GET | /share/{share_token} | Public: open a shared diagram by token, no sign-in required (used by guests) |
| GET/POST | /gallery | List the caller's gallery items (without payloads; `?query=` words in the name, tags and description, `?kind=shapes\|image`, `?tag=`, `?limit=`, `?include_thumbnails=false`) / save a selection (`kind=shapes`, tldraw content) or an image (`kind=image`, base64) with a PNG thumbnail, optional `tags` and `description` |
| GET/PATCH/DELETE | /gallery/{id} | Get an item with its payload and size / change its name, tags or description / delete it. Items are private: someone else's item answers 404. See [Personal gallery](#personal-gallery) |
| POST | /diagrams/{id}/gallery-insertions | Insert a copy of one of the caller's gallery items into the diagram (editor): at `x`/`y`, next to `near_shape_id` (`side`, `gap`) or to the right of everything, with `scale`. New ids, recorded in the history and pushed to open editors |
| WS | /ws/diagrams/{id} | Real-time collaboration: broadcasts canvas updates, the other people's pointers (see [Live cursors](#live-cursors)), peer count, saved changes (`diagram_updated`, including those made through the API or the MCP server) and `comments_changed` (no comment text) so open editors reload the comments to everyone connected to the same diagram. An agent that reads or saves the diagram through the MCP server (`X-Agent-Name`, honoured with the service key or a personal key when auth is on) is listed in the presence for 60s after its last call. Guests join with `?share=<token>&name=<name>` as read-only viewers |
| WS | /ws/workspaces/{id}/presence | Who is in each diagram of the workspace, for the sidebar: a snapshot on connect, then batched deltas (see [Sidebar presence](#sidebar-presence)). Signed-in members only (`?token=<ID token>`); share-link guests are refused. Nothing is stored |

All routes except `/health` and `/ready` return `501 Not Implemented` until infra is wired.

## Live cursors

Everyone with a diagram open sees the other people's pointers as coloured arrows with their name, in the editor,
in presentation mode and on a shared link, over the same `/ws/diagrams/{id}` socket as the presence. The colour and
name are the ones of the presence avatars; nobody sees their own pointer, not even from another tab.

Pointers travel in page (canvas) coordinates, so each viewer draws them at their own zoom, pan and window size:

- Client to server, at most ~30 a second and only when the position changes (rounded to 0.1):
  `{"type": "cursor", "point": {"x": 120.5, "y": -40}, "page": "page:page"}`, or `{"type": "cursor", "point": null}`
  when the pointer leaves the canvas.
- Server to the other connections of the same diagram, stamped with the sender's presence id and name (a client
  cannot speak for someone else): `{"type": "cursor", "id": "<presence id>", "name": "Ana", "point": {...} | null,
  "page": "page:page" | null}`.

The server never stores positions. It validates each message (finite coordinates within ±10,000,000, a tldraw page
id, no extra fields) and relays at most 60 a second per connection, dropping the rest. Receivers ease each cursor
towards its latest position on every animation frame without re-rendering the app, show only the cursors on the page
they are looking at, and drop a cursor when its pointer leaves the canvas, when the person leaves the diagram, when
the connection drops or after 30s without moving. Messages a client does not understand are ignored.

## Sidebar presence

The sidebar shows, next to each diagram, the photos of the people who have it open right now and, next to each
project (even collapsed), everyone in any of its diagrams, each person once. Up to three faces are stacked with a
`+N` for the rest; tooltips and the group's `aria-label` carry the names. Photos come from the same `picture_url`
as the presence avatars (initial on the person's colour when there is none or it fails to load), agents look as they
do in the presence, and share-link guests in a diagram are shown under the name they entered. You are left out of the
sidebar (the top bar already shows you in the open diagram), whether you are in one tab or several.

Each open sidebar holds one socket, `/ws/workspaces/{id}/presence`, whatever the number of diagrams:

- On connect: `{"type": "presence_snapshot", "you": "<your presence id>" | null, "diagrams": [{"diagram_id":
  "...", "project_id": "...", "users": [<presence entries>]}]}`, with only the diagrams someone is in.
- Then: `{"type": "presence_delta", "diagrams": [...]}` with only the diagrams whose people changed, each with its
  full list (`"users": []` when everyone left). Changes are batched for 1s per workspace, so a signed-in person
  who reloads and is back within the batch causes no message, and a burst of joins sends one.
- Presence entries are the ones of the diagram socket: `id`, `name`, `kind` (`person` or `agent`), `picture_url`
  for people and `owner_id`/`owner_name`/`label` for agents with a personal key.

Permissions follow the workspace: any member (viewer and up) can open every diagram of the workspace, so a member
sees the presence of every diagram of that workspace and of no other. The socket needs a signed-in member's ID token;
no token (share-link guests) or a token of someone outside the workspace is refused with close code 1008, and the
membership is checked again every 60s, so someone removed from the workspace stops receiving it without reloading
(a check that fails for another reason closes the socket too). Each person may hold 10 of these sockets at once, and
since the channel only flows from server to client, a client that keeps sending (more than a burst of 10, then 1 a
second) is disconnected. With authentication disabled the socket is open to anyone, like the rest of the API, and
rooms of diagrams that do not exist (only reachable that way) are never shown.
The client reconnects 2s after a drop (30s after a 1008) and shows nobody while disconnected.

## Diagram previews

The diagram cards of a project's overview show a preview of each diagram instead of a generic icon. Previews are
rendered by the editor in the browser, never by the server, and stored apart from the diagram:

- **Rendering.** While someone who can edit has a diagram open, the editor renders its current page with tldraw's
  `toImage` after each saved version (theirs, another editor's or an agent's) and once on open when the stored
  preview is missing or older than the diagram. It waits until 2s have passed without a new version or a local edit,
  so a burst of changes renders once and never mid-gesture. Each render makes a light and a dark
  image with a transparent background, so the card's own background shows in either theme. Images are WebP (PNG in
  browsers that can't encode it), scaled down to fit twice the card size (big diagrams shrink, small ones are never
  enlarged); a render over 64 KiB is retried at half the scale once and otherwise left out. An empty page clears the
  preview. Rendering and uploading run in the background: a failure shows no toast and the card keeps what it had.
- **Storage.** `PUT /diagrams/{id}/thumbnail` writes both themes to `diagram_thumbnails` (one row per diagram and
  theme) in one atomic upsert that only replaces an older `version`, so late, retried or concurrent uploads never
  bring back an older image. The table is separate from `diagrams`, so storing a preview never changes the diagram's
  `updated_at` ("Edited ..." on the card) and opening or listing diagrams never reads the images.
- **Listing.** The overview fetches `GET /projects/{id}/diagrams/thumbnails?theme=` once per visit and theme, next
  to the project tree (which stays lean for the sidebar and the MCP server). Cards show an empty preview area while it
  loads and the placeholder icon for diagrams without a preview (empty, or never opened by an editor since previews
  exist: the first editor who opens one renders it).
- **Permissions.** Reading previews needs workspace membership, like the listing; storing one needs the editor role,
  and the editor only renders for owners and editors (nobody while the role is still loading). Viewers, share-link
  guests and the public `/share/{token}` payload are unchanged: they never write previews nor receive them.

## Diagram history and personal API keys

Every saved change to a diagram is kept in `diagram_revisions` as a full snapshot (name, canvas, shape metadata)
with its author, origin (`human` or `agent`), an optional summary and timestamps. The editor's *History* tab lists
them with a preview, and editors and owners can restore any of them; viewers only look.

To keep the table small:

- A person's saves (the editor autosaves every few seconds) update their own revision for
  `REVISION_INTERVAL_MINUTES`, so each person gets at most one revision per interval, even when several people
  edit together.
- Every agent change (`update_diagram`, `edit_shapes`) and every restore gets a revision of its own, and the state
  right before it is captured first (as a `baseline`) when the history doesn't already end with it.
- Saves that change nothing (e.g. `{}` versus no metadata) don't add revisions.
- After each write, revisions beyond `REVISION_MAX_PER_DIAGRAM` or older than `REVISION_RETENTION_DAYS` are deleted.

A restore brings back the canvas and shape metadata (name and folder stay), is recorded as a new `restore` revision
and is pushed to every open editor, so it can itself be undone.

People create **personal API keys** from the user menu (*API keys* or *Connect Claude*). Each has a label and a
last-used time; the secret (`mcpk_...`) is shown once and only its SHA-256 hash is stored. A key acts as its owner,
with their role, but can't manage keys. Agents using one show up as *Ana's Claude* in the presence avatars and the
history, so two people's agents are two different avatars. The shared `SERVICE_API_KEY` still works as an agent
without owner.

## Validation of agent-generated code

Three deterministic checks catch what unit tests with mocks miss. Agents run `make smoke` and
`make lint-imports` before opening a PR (see `CLAUDE.md`). Their results, with every other CI analysis, land
in a single [Quality Report](#quality-report) comment on the PR.

### Boot smoke (`make smoke`, CI job `smoke`)

`scripts/smoke.sh` starts a throwaway Postgres container (same image as `docker-compose.yaml`, no
volume, so it is always empty), migrates it up to the previous revision, seeds a gallery item, runs
`alembic upgrade head` over it (then downgrades and upgrades the newest migration again) and starts the real API with
`.env.example` plus these modes:

| Mode | Settings | Checks |
|---|---|---|
| production-guard | `ENV=production`, `AUTH_ENABLED=false` | the API refuses to start |
| auth-enabled | `ENV=production`, `AUTH_ENABLED=true`, a random `SERVICE_API_KEY` | `/health`, `/ready`, `/openapi.json`; `401` without credentials; workspace → project → diagram → revision with the service key; the service key gets `403` on the gallery; then the MCP smoke against this API |
| auth-disabled | `ENV=development`, `AUTH_ENABLED=false` | the same probes and CRUD walk; gallery tags, search and an insertion next to a shape; then the MCP smoke on the gallery tools |
| database-down | database URL pointing to a closed port | `/health` stays `200`, `/ready` answers `503` |

It also runs `alembic check` (models versus migrations) and fails on drift; set `SMOKE_STRICT_SCHEMA=0`
to only print a warning while working on a migration. On any failure it prints the API and Postgres logs, and it
always removes the container and stops the processes.

`scripts/smoke_mcp.sh` (`make smoke-mcp`) starts `mcp/server.py` in streamable-http mode and checks
`/health`, the MCP `initialize` handshake, `tools/list`, that a foreign `Host` is rejected (`421`) and,
when given an API, that `tools/call list_workspaces` reaches it. With `SMOKE_MCP_GALLERY=service` it checks that
the gallery tools explain the service key has no gallery; with `personal`, it lists, describes, inserts and tags
gallery items and reads the diagram and its history back.

| Variable | Default | Description |
|---|---|---|
| `SMOKE_DATABASE_URL` | - | Use this **empty** database instead of starting a container (no docker needed) |
| `SMOKE_POSTGRES_IMAGE` | image of `db` in `docker-compose.yaml` | Postgres image of the throwaway container |
| `SMOKE_TIMEOUT` | `60` | Seconds to wait for Postgres, the API and the MCP server |
| `SMOKE_STRICT_SCHEMA` | `1` | `0` turns `alembic check` drift into a warning instead of failing the smoke |
| `SMOKE_SKIP_MCP` | `0` | `1` skips the MCP smoke inside `make smoke` |

### Static analysis thresholds (`make hooks`, CI jobs `lint` and `quality`)

The backend holds the strictest setting of every tool, with no baseline, per-file ignore, `# noqa`,
`# type: ignore` or vulture allowlist. A regression fails pre-commit and CI.

The only suppressions are five line-scoped `# nosec` in `scripts/`, where running a process is the job:
`B404` (importing `subprocess`) and `B603` (a process started without a shell) in `quality_report.py`
(`run <analysis> -- <command>` runs the CI analysis commands) and `mutation.py` (`git` and `mutmut`, resolved
to absolute paths with `shutil.which`). Bandit flags every `subprocess` call at low severity whatever its
input, so these are reviewed call sites, not tolerated findings; nothing else may be suppressed.

| Tool | Scope | Threshold |
|---|---|---|
| ruff (lint + format) | whole repository | zero findings (`E`, `F`, `I`, `UP`, `B`, `SIM`) |
| mypy | `app`, `tests`, `scripts`; `mcp/` | `strict = true`, zero errors |
| bandit | `app`, `mcp/`, `scripts/` (not `mcp/tests`) | zero findings at **every** severity (no `-ll`) |
| vulture | `app` | zero findings at confidence 80, **blocking** (no longer advisory) |
| xenon | `app`, `mcp/`, `scripts/` (not `mcp/tests`) | rank **A** absolute, per module and on average (`--max-absolute A --max-modules A --max-average A`) |
| import-linter | `app`, `mcp/` | every contract, no `ignore_imports` |
| coverage | `app` | line **and** branch coverage, `fail_under = 95` (ratchet, baseline 95.7%) |
| mutmut | use cases and domain services | `MUTATION_MIN_SCORE` ratchet, see below |

Thresholds are ratchets: raise them when the code allows it, never lower them to get a PR green.

### Architecture contracts (`make lint-imports`)

[import-linter](https://import-linter.readthedocs.io/) contracts live in `[tool.importlinter]` of
`pyproject.toml` (API) and `mcp/pyproject.toml` (MCP server) and run in pre-commit and CI:

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

### Mutation testing (`make mutation-changed` on PRs, `make mutation` weekly)

[mutmut](https://mutmut.readthedocs.io/) changes the code one small edit at a time (a `<` becomes `<=`, an
argument becomes `None`...) and runs the unit tests against each change. The scope is `only_mutate` in
`[tool.mutmut]` of `pyproject.toml`: `app/domain/usecases/` and `app/domain/services/`.

- **On every PR** (CI job `mutation`, `make mutation-changed` locally): `scripts/mutation.py changed` diffs
  the branch against the base, keeps the files in scope and maps the changed lines to the functions and
  methods that contain them, so only their mutants run. A change outside any function (a constant, a class
  attribute) mutates the whole file; imports, blank lines and comments are ignored. The job fails when the
  score of what it mutated is below `MUTATION_MIN_SCORE`, and the Quality Report lists the survivors of the
  changed code with their diffs. It has a 20-minute timeout and caches `mutants/`.
- **Weekly** (*Mutation testing* workflow, Mondays 06:00 UTC, and on demand with `workflow_dispatch` and an
  optional minimum score): mutates the whole scope (about 2,700 mutants, 5 to 10 minutes locally) and publishes the
  per-package and per-file report in the job summary and the `mutation-report` artifact. It never gates.

`MUTATION_MIN_SCORE` is a **ratchet**: a floor a bit below the current baseline, 95 by default. The first
full run scored 67.7% (ratchet 60); the whole scope now scores 100% (2,704 mutants) with no surviving mutant, and the
floor stays a little below 100% because the PR job scores only the few functions a change touches, where a
single mutant that no test can tell apart (an equivalent mutant) weighs a lot. It only goes up: raise it as tests improve, in the repository variable
`MUTATION_MIN_SCORE` (Settings → Secrets and variables → Actions → Variables) or the default in
`scripts/mutation.py` and `ci.yml`. To change what is mutated, edit `only_mutate`; both runs follow it.

Reading the result (`mutants/report.md` locally, job summary and `mutation-report` artifact in CI):

- **killed**: a test failed, so the tests pin that behaviour down (timeouts count as killed);
- **survived**: every test still passed, so nothing checks that line; `uv run mutmut show <name>` prints the diff;
- **no tests**: no unit test runs that code at all (counts as not killed);
- **score** = killed / all mutants. Survivors that only change an error message are usually noise; survivors
  that change a comparison, a condition or the id passed to a repository are real gaps.

Results are cached in `mutants/` (git-ignored): the next run only re-tests what changed. Delete it for a
clean run; `uv run mutmut browse` explores the results interactively.

### Quality Report

Every PR gets **one** comment titled *Quality Report* (found and updated through the
`<!-- quality-report -->` marker), rebuilt on each push by the `quality-report` job:

- the top line is the verdict (❌ failed, ⚠️ passed with warnings, ✅ all good) and the table has one row per
  analysis: backend lint/format, types (API and MCP), security, dead code, complexity, tests and coverage
  (API and MCP), architecture contracts (API and MCP), boot smoke, mutation testing, and the frontend lint,
  types, tests with coverage and build;
- each section below has the summary and, in a collapsed `<details>`, the evidence: least covered files,
  broken contracts with the violating import, smoke scenarios with their boot time, surviving mutants with
  their diffs, lint problems, failures;
- ✅ passed, ⚠️ warning (ESLint warnings or models/migrations drift reported without failing, as with
  `SMOKE_STRICT_SCHEMA=0`; in CI both fail the job), ❌ failed,
  ⏭️ not run (job cancelled or skipped, or nothing to mutate). A job that failed before producing its result
  shows as ❌ with the job result, so the report never breaks.

The report only informs: each job is still the gate for its own checks, with the same thresholds. It is also
written to the job summary, which is the only place it appears on PRs from forks (their token cannot
comment).

How it works: each job runs its tools through `scripts/quality_report.py run <analysis> -- <command>`, which
streams the output, keeps the exit code and stores a JSON fragment in `quality-fragments/`; the job uploads it
as the `quality-fragment-<job>` artifact. The `quality-report` job (`needs` every analysis job, `if: always()`)
downloads them and runs `scripts/quality_report.py render`. To add an analysis:

1. add a value to `Analysis` and an `analyze_<tool>` function returning a `Finding` in
   `scripts/quality_report.py`, registered in `ANALYZERS`;
2. add a `Check` to a `Section` in `SECTIONS` (or a new `Section`), with the job that runs it;
3. in `ci.yml`, run the tool through the wrapper (`if: ${{ !cancelled() }}` when it is not the first step),
   upload `quality-fragments/` as `quality-fragment-<job>` and, for a new job, add it to the `needs` of
   `quality-report`;
4. add tests in `tests/unit/scripts/test_quality_report.py` with a sample of the tool's real output.

## Comments

Comments are plain text (never rendered as HTML or Markdown), anchored to a shape through `element_id` or to the
whole diagram. Control characters and bidirectional overrides are dropped, and the text is limited to 5000
characters. Each comment records who wrote it with the same identity rules as the history: a person, an agent with
a personal key (shown as *Ana's Claude*, with an agent mark and the key's label), or an ownerless agent on the
shared `SERVICE_API_KEY`.

A comment is open until someone resolves it; it can be reopened, and the editor shows who resolved it and when.
The *Comments* tab hides resolved comments behind *Show resolved* and dims them, and the pins on the canvas and the
tab count only open comments.

| Action | People | Agents (MCP server) |
|---|---|---|
| Read | Any member | Any member (the key owner's role) |
| Create | Editor or owner | Editor or owner |
| Resolve / reopen | Editor or owner, any comment | Editor or owner, any comment (it's reversible and recorded) |
| Delete | Editor or owner, any comment | Editor or owner, and only comments written with **the same key** |

The backend enforces these rules; the MCP tools only describe them. The shared service key keeps skipping workspace
roles, as for every other route, but it can only delete the comments written with it. Creating, resolving,
reopening and deleting are logged at `INFO` with who did it (never the text).

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
| History | `list_revisions`, `restore_revision` |
| Organisation | `create_project`, `create_folder` |
| Documentation and comments | `get_documentation`, `update_documentation`, `list_comments`, `add_comment`, `resolve_comment`, `reopen_comment`, `delete_comment` |
| Personal gallery | `list_gallery_items`, `get_gallery_item`, `insert_gallery_item`, `update_gallery_item` (a personal key when auth is on) |

Nothing deletes workspaces, projects, folders or diagrams (`edit_shapes` only deletes shapes inside a canvas, and
`delete_comment` only the comments the agent's own key wrote), and nothing manages members. On connect the server sends instructions telling the agent to call `open_link` when it sees
a link to the app (named after `APP_NAME`), and to prefer the compact tools below over whole canvases.

Configure the backend URL with `MCP_API_URL` (default: `http://localhost:8000`). When the API has `AUTH_ENABLED=true`, set `MCP_API_KEY` to the API's `SERVICE_API_KEY`, or to a personal key so the agent acts as you.

`update_diagram` and `edit_shapes` take an optional `summary` shown in the diagram's history (a generic one is made
up when it's missing). Over HTTP, the key sent by the MCP client in `X-API-Key` (or `Authorization: Bearer`) is used
instead of `MCP_API_KEY`, so one shared MCP server serves everyone under their own name. The frontend's *Connect
Claude* dialog generates the key and the ready-to-paste commands:

```sh
claude mcp add --transport http drawdoro http://localhost:8001/mcp --header "X-API-Key: mcpk_..."
```

`update_diagram` only changes the fields you pass; the others keep their current values. A canvas is tens of KB of
tldraw JSON, so agents mostly use three tools that avoid moving it around:

- `get_diagram_outline`: every shape with its position, size, colour and plain text, in reading order.
- `edit_shapes`: creates, changes (JSON Merge Patch) or deletes only the given records, with an optional
  `expected_updated_at` guard against overwriting someone else's save. Deleting a shape also deletes its children and
  arrow bindings.
- `render_diagram`: a PNG of the whole canvas, some shapes or a region. The MCP server opens the frontend's `/render`
  page (`MCP_FRONTEND_URL`) in a headless Chromium, so the image matches the editor exactly. Locally, install the
  browser once with `cd mcp && uv run playwright install --only-shell chromium` and keep the frontend running.

Comments are how people ask the agent for changes: `list_comments` (`status="open"` for the pending ones) returns
each comment's id, author (person or agent, with the person it works for), anchored `element_id`, status, who
resolved it and when, and `created_by_you`. The agent answers with `add_comment` and closes what it addressed with
`resolve_comment` (anyone's comment, reversible with `reopen_comment`); `delete_comment` is refused for anything its
key didn't write. The comment text comes in an `untrusted_user_content` field next to a `notice` saying it is data,
not instructions, and the tool descriptions and server instructions say the same. That lowers the risk of prompt
injection through comments but can't rule it out: the real limits are the backend permissions above.

### Personal gallery

The gallery holds what each person saved for reuse: selections of shapes and images (PNG, JPEG, GIF or WebP).
Items have a name, up to 10 tags (stored in lower case) and an optional description, edited and searched in the
editor's *Gallery* panel. It is personal: every route works on the caller's own items, someone else's item answers
`404`, and the shared service key (no owner) gets `403` with a message asking for a personal key. With
`AUTH_ENABLED=false` the items without owner form one shared gallery.

Agents reach it with a personal key: `list_gallery_items` (search by name, tag or description, filter by kind, up to
100 items per call; never image data), `get_gallery_item` (what a "shapes" item contains, or an image's size),
`update_gallery_item` (name, tags, description) and `insert_gallery_item`. The tool descriptions and the server
instructions tell the agent to look in the gallery before drawing a logo, an icon or a component from scratch.
Names, tags, descriptions and texts come in `untrusted_user_content` / `untrusted_text` next to a `notice` saying
they are data, not instructions.

Insertion runs in the API (`POST /diagrams/{id}/gallery-insertions`), so people and agents share the same rules: it
needs the editor role in the diagram's workspace, copies every shape, binding and asset with new ids (arrows stay
connected, nothing is overwritten), keeps the layout, places the copy where asked without covering shapes, refuses
items whose record versions differ from the diagram's tldraw schema (the server doesn't migrate records), and is recorded in the history (as the agent, with the
person it works for) and pushed to open editors. Positions must be finite and within a billion units of the origin,
the scale between 0.1 and 10, and the diagram must stay within 4000 shapes and `GALLERY_MAX_CANVAS_BYTES`; items whose
shapes repeat an id or don't all hang from a top-level shape are refused rather than copied as a broken tree. Images are embedded in the canvas as a `data:` URL built from the
stored bytes, whose type was detected from their content on upload, so no external URL is ever fetched or stored.

### Available tools

The *Connect Claude* dialog has an *Available tools* tab listing every MCP tool by area, with search, a button to
copy the name and badges for the tools that need a personal key or the editor role. It reads
`frontend/src/config/mcpTools.json`, generated from the server's real tool registry (`mcp/catalog.py` holds each
tool's area and requirements, the docstrings hold the descriptions) by `make mcp-manifest`; `mcp/tests/test_manifest.py`
and a pre-commit hook fail when the file is out of date.

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
