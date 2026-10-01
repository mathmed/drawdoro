#!/usr/bin/env bash
# Boot smoke test: migrates a clean Postgres, starts the real API with production-like settings and
# checks it answers. Brand-neutral on purpose: names come from .env.example (APP_SLUG), so the same
# script runs unchanged in every fork.
#
# Modes, in order:
#   production-guard  ENV=production with AUTH_ENABLED=false must refuse to start
#   auth-enabled      ENV=production, AUTH_ENABLED=true (how production runs); also runs the MCP
#                     smoke against this API with the service key, which has no gallery
#   auth-disabled     ENV=development, AUTH_ENABLED=false (local development); also runs the MCP
#                     smoke on the gallery: list, describe, insert into a diagram and tag
#   database-down     /health stays 200 and /ready answers 503 when the database is unreachable
#
# Environment:
#   SMOKE_DATABASE_URL    use this empty database instead of starting a throwaway Postgres container
#                         (CI passes its service container). It must be clean: migrations run on it.
#   SMOKE_POSTGRES_IMAGE  image of the throwaway container (default: the one in docker-compose.yaml)
#   SMOKE_TIMEOUT         seconds to wait for each process to become ready (default: 60)
#   SMOKE_STRICT_SCHEMA   1 makes `alembic check` (models vs migrations drift) fail the smoke
#   SMOKE_SKIP_MCP        1 skips the MCP smoke
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TIMEOUT="${SMOKE_TIMEOUT:-60}"
WORK="$(mktemp -d)"
API_PID=""
API_LOG=""
DB_CONTAINER=""
BODY=""
SMOKE_DIAGRAM_ID=""

log() { printf '\n>> %s\n' "$*"; }

dump_logs() {
    if [[ -n "$API_LOG" && -f "$API_LOG" ]]; then
        printf '\n----- API log (%s) -----\n' "$API_LOG" >&2
        tail -n 200 "$API_LOG" >&2 || true
    fi
    if [[ -n "$DB_CONTAINER" ]]; then
        printf '\n----- Postgres log -----\n' >&2
        docker logs --tail 50 "$DB_CONTAINER" >&2 || true
    fi
}

fail() {
    printf '\n!! SMOKE FAILED: %s\n' "$*" >&2
    dump_logs
    exit 1
}

stop_api() {
    [[ -z "$API_PID" ]] && return 0
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
    API_PID=""
}

cleanup() {
    stop_api
    [[ -n "$DB_CONTAINER" ]] && docker rm -f "$DB_CONTAINER" >/dev/null 2>&1
    rm -rf "$WORK"
}
trap cleanup EXIT

# Exports .env.example literally (no shell expansion), so JSON values such as CORS_ORIGINS survive.
load_env_example() {
    local line
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ -z "$line" || "$line" == \#* ]] && continue
        export -- "${line?}"
    done < "$ROOT/.env.example"
}

free_port() {
    python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'
}

json_field() {
    python3 -c 'import json, sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$1" "$2"
}

# request METHOD URL EXPECTED_STATUS [JSON_BODY] [CURL_ARGS...]; the response body lands in $BODY.
request() {
    local method="$1" url="$2" expected="$3" data="${4:-}"
    shift 4 2>/dev/null || shift $#
    local args=(-s -o "$WORK/body" -w '%{http_code}' -X "$method" "$@")
    [[ -n "$data" ]] && args+=(-H 'Content-Type: application/json' --data "$data")
    local status
    status="$(curl "${args[@]}" "$url")" || status="000"
    BODY="$(cat "$WORK/body" 2>/dev/null || true)"
    if [[ "$status" != "$expected" ]]; then
        fail "$method $url answered $status, expected $expected. Body: ${BODY:0:500}"
    fi
    printf '   ok  %-6s %-60s %s\n' "$method" "${url#http://127.0.0.1:*/}" "$status"
}

elapsed_since() {
    awk -v start="$1" -v now="$EPOCHREALTIME" 'BEGIN { printf "%.1f", now - start }'
}

# The "ready in" line is read by scripts/quality_report.py for the Quality Report.
wait_for() {
    local url="$1" pid="$2" name="$3" deadline=$((SECONDS + TIMEOUT)) started="$EPOCHREALTIME"
    until curl -sf -o /dev/null "$url"; do
        kill -0 "$pid" 2>/dev/null || fail "$name exited before answering $url"
        ((SECONDS < deadline)) || fail "$name did not answer $url within ${TIMEOUT}s"
        sleep 0.5
    done
    printf '   ok  %s ready in %ss\n' "$name" "$(elapsed_since "$started")"
}

start_database() {
    if [[ -n "${SMOKE_DATABASE_URL:-}" ]]; then
        log "Using the database from SMOKE_DATABASE_URL"
        DATABASE_URL="$SMOKE_DATABASE_URL"
        return
    fi
    command -v docker >/dev/null || fail "docker is required (or set SMOKE_DATABASE_URL)"
    local image="${SMOKE_POSTGRES_IMAGE:-}"
    if [[ -z "$image" ]]; then
        image="$(grep -m1 -oE 'image: *postgres:[^[:space:]]+' docker/docker-compose.yaml | awk '{print $2}')"
    fi
    DB_CONTAINER="${APP_SLUG:-app}-smoke-db-$$"
    log "Starting a throwaway $image ($DB_CONTAINER)"
    # No volume: every run migrates an empty database, like a fresh environment would.
    docker run -d --rm --name "$DB_CONTAINER" \
        -e POSTGRES_USER=smoke -e POSTGRES_PASSWORD=smoke -e POSTGRES_DB=smoke \
        -p 127.0.0.1::5432 "$image" >/dev/null || fail "could not start Postgres"
    local deadline=$((SECONDS + TIMEOUT))
    # -h forces TCP: the entrypoint's temporary server only listens on the unix socket.
    until docker exec "$DB_CONTAINER" pg_isready -q -U smoke -h 127.0.0.1; do
        ((SECONDS < deadline)) || fail "Postgres did not become ready within ${TIMEOUT}s"
        sleep 1
    done
    local port
    port="$(docker port "$DB_CONTAINER" 5432/tcp | head -n1 | awk -F: '{print $NF}')"
    DATABASE_URL="postgresql+asyncpg://smoke:smoke@127.0.0.1:${port}/smoke"
}

alembic_run() {
    DATABASE_URL="$DATABASE_URL" uv run --locked alembic "$@" > "$WORK/alembic.log" 2>&1 \
        || { cat "$WORK/alembic.log" >&2; fail "alembic $* failed"; }
    grep -E 'Running (upgrade|downgrade)' "$WORK/alembic.log" | sed -E 's/^.*Running (upgrade|downgrade)/   \1/' || true
}

# sql STATEMENT: runs one statement on the smoke database and prints the first column of each row.
sql() {
    SMOKE_SQL="$1" uv run --locked python - <<'PY'
import asyncio
import os

import asyncpg


async def main() -> None:
    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    connection = await asyncpg.connect(url)
    try:
        for row in await connection.fetch(os.environ["SMOKE_SQL"]):
            print(row[0])
    finally:
        await connection.close()


asyncio.run(main())
PY
}

# The gallery migration (0008) runs over an item saved before tags existed: the item must keep
# working, without tags and with its size filled in, and the migration must be reversible.
LEGACY_ITEM_ID="00000000-0000-4000-8000-000000000008"

migrate() {
    log "alembic upgrade 0007 (clean database), then a gallery item saved before tags existed"
    alembic_run upgrade 0007
    sql "INSERT INTO gallery_items (id, owner_id, name, kind, content)
         VALUES ('$LEGACY_ITEM_ID', NULL, 'Legacy item', 'shapes',
                 '{\"shapes\": [{\"id\": \"shape:legacy\"}]}') RETURNING id" > /dev/null \
        || fail "could not seed the legacy gallery item"

    log "alembic upgrade head (over existing data)"
    alembic_run upgrade head
    local legacy
    legacy="$(sql "SELECT CAST(tags AS text) || ' ' || size_bytes FROM gallery_items WHERE id = '$LEGACY_ITEM_ID'")"
    [[ "$legacy" =~ ^\[\]\ [0-9]+$ ]] || fail "the legacy gallery item was not migrated: '$legacy'"
    echo "   ok  existing gallery item kept, without tags, size filled in"

    log "alembic downgrade -1 and upgrade head again (the newest migration is reversible)"
    alembic_run downgrade -1
    alembic_run upgrade head

    log "alembic check (SQLAlchemy models vs migrations)"
    if DATABASE_URL="$DATABASE_URL" uv run --locked alembic check > "$WORK/check.log" 2>&1; then
        echo "   ok  models match the migrations"
    elif [[ "${SMOKE_STRICT_SCHEMA:-0}" == "1" ]]; then
        cat "$WORK/check.log" >&2
        fail "models and migrations drifted (alembic check)"
    else
        echo "   WARNING: models and migrations drifted (set SMOKE_STRICT_SCHEMA=1 to fail):"
        grep -E 'Detected|FAILED' "$WORK/check.log" | sed 's/^/     /' || true
    fi
}

# start_api NAME [VAR=VALUE...]: starts uvicorn with .env.example plus the overrides.
start_api() {
    local name="$1"
    shift
    API_LOG="$WORK/api-$name.log"
    API_PORT="$(free_port)"
    API_URL="http://127.0.0.1:$API_PORT"
    env "$@" uv run --locked uvicorn app.main.main:app --host 127.0.0.1 --port "$API_PORT" \
        > "$API_LOG" 2>&1 &
    API_PID=$!
    wait_for "$API_URL/health" "$API_PID" "API ($name)"
}

check_probes() {
    request GET "$API_URL/health" 200
    [[ "$(json_field "$BODY" status)" == "ok" ]] || fail "/health body: $BODY"
    request GET "$API_URL/ready" 200
    [[ "$(json_field "$BODY" status)" == "ready" ]] || fail "/ready body: $BODY"
    request GET "$API_URL/openapi.json" 200
}

# Comment lifecycle on the newest columns: create, resolve, filter by status, delete.
check_comments() {
    local diagram_id="$1"
    shift
    local base="$API_URL/diagrams/$diagram_id/comments" comment_id
    request POST "$base" 201 '{"element_id": "shape:smoke", "content": "Smoke <b>comment</b>"}' "$@"
    comment_id="$(json_field "$BODY" id)"
    [[ "$(json_field "$BODY" content)" == "Smoke <b>comment</b>" ]] || fail "comment text changed: $BODY"
    request PATCH "$base/$comment_id" 200 '{"resolved": true}' "$@"
    [[ "$(json_field "$BODY" resolved)" == "True" ]] || fail "comment not resolved: $BODY"
    request GET "$base?status=resolved" 200 "" "$@"
    [[ "$BODY" == *"$comment_id"* ]] || fail "resolved comment missing from ?status=resolved: $BODY"
    request GET "$base?status=open" 200 "" "$@"
    [[ "$BODY" == "[]" ]] || fail "resolved comment listed as open: $BODY"
    request PATCH "$base/$comment_id" 200 '{"resolved": false}' "$@"
    request DELETE "$base/$comment_id" 204 "" "$@"
}

# Walks workspace -> project -> diagram -> revision and comments so the newest tables and indexes
# get used. Leaves the diagram id in SMOKE_DIAGRAM_ID for the MCP smoke.
check_crud() {
    local slug="$1"
    shift
    request POST "$API_URL/workspaces" 201 "{\"name\": \"Smoke $slug\", \"slug\": \"smoke-$slug\"}" "$@"
    local workspace_id project_id diagram_id
    workspace_id="$(json_field "$BODY" id)"
    request POST "$API_URL/workspaces/$workspace_id/projects" 201 '{"name": "Smoke"}' "$@"
    project_id="$(json_field "$BODY" id)"
    request POST "$API_URL/projects/$project_id/diagrams" 201 '{"name": "Smoke"}' "$@"
    diagram_id="$(json_field "$BODY" id)"
    request PUT "$API_URL/projects/$project_id/diagrams/$diagram_id" 200 \
        '{"name": "Smoke", "canvas_state": {"store": {}}, "revision_summary": "smoke"}' "$@"
    request GET "$API_URL/diagrams/$diagram_id/revisions" 200 "" "$@"
    check_comments "$diagram_id" "$@"
    SMOKE_DIAGRAM_ID="$diagram_id"
    request GET "$API_URL/projects/$project_id/tree" 200 "" "$@"
    request GET "$API_URL/projects/$project_id/diagrams" 200 "" "$@"
    request GET "$API_URL/workspaces" 200 "" "$@"
}

# Writes the payloads of the gallery checks to $WORK: a canvas as the editor saves it (tldraw 3.15
# records, with an anchor shape), a group of two boxes joined by an arrow, and a small PNG.
write_gallery_payloads() {
    SMOKE_WORK="$WORK" uv run --locked python - <<'PY'
import base64
import json
import os
from pathlib import Path

from tests.tldraw_records import arrow, binding, canvas, content, geo, group, png

work = Path(os.environ["SMOKE_WORK"])
diagram = {"name": "Smoke", "canvas_state": canvas(geo("shape:smoke", 0, 0, 200, 80)), "revision_summary": "smoke canvas"}
shapes = content(
    [
        group("shape:g", 0, 0),
        geo("shape:a", 0, 0, 100, 50, parent="shape:g", index="a1"),
        geo("shape:b", 300, 0, 100, 50, parent="shape:g", index="a2"),
        arrow("shape:arrow", 100, 25, (200, 0), index="a3") | {"parentId": "shape:g"},
    ],
    bindings=[
        binding("binding:start", "shape:arrow", "shape:a", "start"),
        binding("binding:end", "shape:arrow", "shape:b", "end"),
    ],
)
items = {
    "shapes-item": {"name": "Smoke service", "kind": "shapes", "content": shapes, "tags": ["Smoke", "Service"]},
    "image-item": {"name": "Smoke logo", "kind": "image", "image_base64": base64.b64encode(png(48, 24)).decode()},
}
(work / "canvas.json").write_text(json.dumps(diagram))
for name, item in items.items():
    (work / f"{name}.json").write_text(json.dumps(item))
PY
}

# Gallery on the newest columns: the migrated item, tags, search, and a server-side insertion.
# Leaves the item ids in SMOKE_SHAPES_ITEM_ID and SMOKE_IMAGE_ITEM_ID for the MCP smoke.
check_gallery() {
    local diagram_id="$1" project_id
    write_gallery_payloads || fail "could not write the gallery payloads"
    request GET "$API_URL/diagrams/$diagram_id" 200
    project_id="$(json_field "$BODY" project_id)"
    request PUT "$API_URL/projects/$project_id/diagrams/$diagram_id" 200 "$(cat "$WORK/canvas.json")"
    request GET "$API_URL/gallery/$LEGACY_ITEM_ID" 200
    [[ "$(json_field "$BODY" tags)" == "[]" ]] || fail "the migrated item has tags: $BODY"
    request POST "$API_URL/gallery" 201 "$(cat "$WORK/shapes-item.json")"
    SMOKE_SHAPES_ITEM_ID="$(json_field "$BODY" id)"
    [[ "$(json_field "$BODY" tags)" == "['smoke', 'service']" ]] || fail "tags not normalised: $BODY"
    request POST "$API_URL/gallery" 201 "$(cat "$WORK/image-item.json")"
    SMOKE_IMAGE_ITEM_ID="$(json_field "$BODY" id)"
    [[ "$(json_field "$BODY" width)" == "48.0" ]] || fail "image not measured: ${BODY:0:300}"
    request PATCH "$API_URL/gallery/$SMOKE_IMAGE_ITEM_ID" 200 '{"tags": ["Logo"], "description": "Smoke"}'
    request GET "$API_URL/gallery?tag=logo&include_thumbnails=false" 200
    [[ "$BODY" == *"$SMOKE_IMAGE_ITEM_ID"* && "$BODY" != *"$SMOKE_SHAPES_ITEM_ID"* ]] \
        || fail "search by tag: $BODY"
    request POST "$API_URL/diagrams/$diagram_id/gallery-insertions" 201 \
        "{\"item_id\": \"$SMOKE_SHAPES_ITEM_ID\", \"near_shape_id\": \"shape:smoke\", \"side\": \"below\"}"
    [[ "$(json_field "$BODY" y)" == "160.0" ]] || fail "inserted at the wrong place: $BODY"
}

load_env_example
start_database
export DATABASE_URL
migrate

log "Mode production-guard: ENV=production, AUTH_ENABLED=false must not start"
if env ENV=production AUTH_ENABLED=false uv run --locked python -c "import app.main.main" \
    > "$WORK/guard.log" 2>&1; then
    fail "the API started in production with authentication disabled"
fi
grep -q "AUTH_ENABLED must be true in production" "$WORK/guard.log" \
    || { cat "$WORK/guard.log" >&2; fail "the production guard failed for another reason"; }
echo "   ok  refused to start"

log "Mode auth-enabled: ENV=production, AUTH_ENABLED=true"
SERVICE_KEY="smoke-$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
start_api auth-enabled ENV=production AUTH_ENABLED=true SERVICE_API_KEY="$SERVICE_KEY" \
    COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID:-us-east-1_smoke}" \
    COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID:-smoke-client}"
check_probes
request GET "$API_URL/workspaces" 401
request GET "$API_URL/workspaces" 401 "" -H "X-API-Key: wrong-key"
check_crud auth-enabled -H "X-API-Key: $SERVICE_KEY"
# The gallery is personal: the shared service key has no owner, so it has no gallery.
request GET "$API_URL/gallery" 403 "" -H "X-API-Key: $SERVICE_KEY"
[[ "$BODY" == *"personal API key"* ]] || fail "the service key got no explanation: $BODY"
if [[ "${SMOKE_SKIP_MCP:-0}" != "1" ]]; then
    SMOKE_MCP_API_URL="$API_URL" SMOKE_MCP_API_KEY="$SERVICE_KEY" \
        SMOKE_MCP_DIAGRAM_ID="$SMOKE_DIAGRAM_ID" SMOKE_MCP_GALLERY=service \
        "$ROOT/scripts/smoke_mcp.sh" || fail "MCP smoke failed"
fi
stop_api

log "Mode auth-disabled: ENV=development, AUTH_ENABLED=false"
start_api auth-disabled ENV=development AUTH_ENABLED=false
check_probes
check_crud auth-disabled
check_gallery "$SMOKE_DIAGRAM_ID"
if [[ "${SMOKE_SKIP_MCP:-0}" != "1" ]]; then
    SMOKE_MCP_API_URL="$API_URL" SMOKE_MCP_DIAGRAM_ID="$SMOKE_DIAGRAM_ID" SMOKE_MCP_GALLERY=personal \
        SMOKE_MCP_SHAPES_ITEM_ID="$SMOKE_SHAPES_ITEM_ID" SMOKE_MCP_IMAGE_ITEM_ID="$SMOKE_IMAGE_ITEM_ID" \
        "$ROOT/scripts/smoke_mcp.sh" || fail "MCP smoke failed"
fi
stop_api

log "Mode database-down: liveness stays up, readiness reports the outage"
start_api database-down ENV=development AUTH_ENABLED=false \
    DATABASE_URL="postgresql+asyncpg://smoke:smoke@127.0.0.1:$(free_port)/smoke"
request GET "$API_URL/health" 200
request GET "$API_URL/ready" 503
stop_api

log "Smoke passed"
