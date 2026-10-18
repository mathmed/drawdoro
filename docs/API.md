# API

The backend serves its OpenAPI schema at `/openapi.json`. Every route requires a signed-in user or an API key
when `AUTH_ENABLED=true`, except `/health`, `/ready` and the public `/share/{share_token}` (see
[Authentication](AUTHENTICATION.md)).

## Health checks

`curl http://localhost:8000/health` (liveness, never touches the database) and
`curl http://localhost:8000/ready` (readiness: `503` while the database is unreachable). Deploy probes depend on
both: never remove or rename them.

## Routes (placeholder)

| Method | Path | Description |
|---|---|---|
| GET | /me | Signed-in user (creates it on first sign-in), with the profile photo as `picture_url` |
| GET/POST | /workspaces/{id}/members | List members / add a member by email (owner) |
| PUT/DELETE | /workspaces/{id}/members/{user_id} | Change a role (owner) / remove a member (owner, or yourself to leave) |
| GET | /health | Liveness: the process answers (`{"status": "ok"}`); never touches the database |
| GET | /ready | Readiness: `{"status": "ready"}` when the database answers, `503` otherwise |
| GET/POST | /workspaces | List / create workspaces. A `slug` another workspace uses, deleted ones included, answers `409` |
| GET/PUT/DELETE | /workspaces/{id} | Get / update / delete workspace. Same `409` for a taken `slug` |
| GET/POST | /workspaces/{id}/projects | List / create projects |
| GET/PUT/DELETE | /workspaces/{id}/projects/{id} | Get / update / delete project |
| GET/POST | /projects/{id}/folders | List / create folders. A missing project or `parent_folder_id`, or a folder of another project, answers `404` |
| GET/PUT/DELETE | /projects/{id}/folders/{id} | Get / update / delete folder. Moving it under a missing folder, or one of another project, answers `404`; keeping its current parent always works, even once that parent is deleted |
| GET | /projects/{id}/tree | Folders and diagram summaries of a project in one response (the sidebar tree) |
| GET/POST | /projects/{id}/diagrams | List diagram summaries (no canvas or metadata) / create a diagram. A missing project or `folder_id`, or a folder of another project, answers `404` |
| GET | /diagrams/{id} | Get a diagram by its id alone, as in the editor link `/diagrams/<id>` (used by the MCP server's `open_link`) |
| GET | /projects/{id}/diagrams/thumbnails | The previews of the project's diagrams in one theme (`?theme=light`, the default, or `dark`), in one query, for the listing cards: `diagram_id`, `version`, `mime_type` and `image_base64`. Diagrams without a preview are left out. See [Diagram previews](FEATURES.md#diagram-previews) |
| PUT | /diagrams/{id}/thumbnail | Store the light and dark previews of a diagram (editor): `version` (the diagram's `updated_at` they were rendered from), `light_base64` and `dark_base64` (PNG or WebP, up to 64 KiB each; `null` when there is nothing to show). An older version never replaces a newer one. `204` |
| GET/PUT/DELETE | /projects/{id}/diagrams/{id} | Get / update / delete diagram. Every saved update is pushed to open editors as `diagram_updated`; editor tabs send `X-Client-Id` so they skip the echo of their own saves. Moving it to a missing folder, or one of another project, answers `404`; keeping its current folder always works, even once that folder is deleted |
| GET/PUT | /diagrams/{id}/documentation | Get / update documentation page |
| GET/POST | /diagrams/{id}/comments | List comments (`?status=open`, `resolved` or `all`, the default) / create one (editor). Plain text up to 5000 characters; `element_id` is optional (omitted for a comment on the whole diagram) |
| PATCH/DELETE | /diagrams/{id}/comments/{comment_id} | Resolve or reopen (`{"resolved": true}`) / delete a comment (editor). Agents only delete the comments their own key wrote; see [Comments](FEATURES.md#comments) |
| POST | /diagrams/{id}/share | Generate (or return) the diagram's shareable link token |
| GET | /diagrams/{id}/revisions | Diagram history, newest first, without snapshots (`?limit=`, up to 200) |
| GET | /diagrams/{id}/revisions/{revision_id} | One revision with its snapshot (name, canvas and shape metadata) |
| POST | /diagrams/{id}/revisions/{revision_id}/restore | Bring the canvas and shape metadata of a revision back (editor). Recorded as a new revision and pushed to open editors |
| GET/POST | /me/api-keys | List / create the signed-in user's personal API keys. The secret is only in the creation response |
| DELETE | /me/api-keys/{key_id} | Revoke a personal API key |
| GET | /share/{share_token} | Public: open a shared diagram by token, no sign-in required (used by guests) |
| GET/POST | /gallery | List the caller's gallery items (without payloads; `?query=` words in the name, tags and description, `?kind=shapes\|image`, `?tag=`, `?limit=`, `?include_thumbnails=false`) / save a selection (`kind=shapes`, tldraw content) or an image (`kind=image`, base64) with a PNG thumbnail, optional `tags` and `description` |
| GET/PATCH/DELETE | /gallery/{id} | Get an item with its payload and size / change its name, tags or description / delete it. Items are private: someone else's item answers 404. See [Personal gallery](FEATURES.md#personal-gallery) |
| POST | /diagrams/{id}/gallery-insertions | Insert a copy of one of the caller's gallery items into the diagram (editor): at `x`/`y`, next to `near_shape_id` (`side`, `gap`) or to the right of everything, with `scale`. New ids, recorded in the history and pushed to open editors |
| WS | /ws/diagrams/{id} | Real-time collaboration: broadcasts canvas updates, the other people's pointers (see [Live cursors](REALTIME.md#live-cursors)), peer count, saved changes (`diagram_updated`, including those made through the API or the MCP server) and `comments_changed` (no comment text) so open editors reload the comments to everyone connected to the same diagram. An agent that reads or saves the diagram through the MCP server (`X-Agent-Name`, honoured with the service key or a personal key when auth is on) is listed in the presence for 60s after its last call. Guests join with `?share=<token>&name=<name>` as read-only viewers |
| WS | /ws/workspaces/{id}/presence | Who is in each diagram of the workspace, for the sidebar: a snapshot on connect, then batched deltas (see [Sidebar presence](REALTIME.md#sidebar-presence)). Signed-in members only (`?token=<ID token>`); share-link guests are refused. Nothing is stored |

All routes except `/health` and `/ready` return `501 Not Implemented` until infra is wired.

Text sent to the API (names, slugs, descriptions, documentation, revision summaries, comment `element_id`, API key
labels, member e-mails, gallery names and descriptions, the share token) loses its NUL characters (`\u0000`) on the
way in: Postgres can't store them. Length limits apply to the text without them.

## Contract tests

`make contract` (CI job `contract`) runs Schemathesis against `/openapi.json` on the real API: responses must match
the documented status codes and schemas. The deviations found when it was introduced are recorded in
`contract-baseline.json` and only new ones fail; see [API contract](DEVELOPMENT.md#api-contract-schemathesis).
When a route answers a status it does not declare yet, document it with `responses=` on the route.

`make openapi-diff` (CI job `openapi-diff`) compares the schema of a pull request with the one of its base and
fails on breaking changes: routes and response fields are only added, never removed or renamed; see
[Breaking API changes](DEVELOPMENT.md#breaking-api-changes-oasdiff).
