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
# The boot (Postgres, alembic, uvicorn, cleanup) lives in scripts/api_server.sh, shared with
# scripts/contract.sh; its header lists SMOKE_DATABASE_URL, SMOKE_POSTGRES_IMAGE and SMOKE_TIMEOUT.
#
# Environment, besides those:
#   SMOKE_STRICT_SCHEMA   0 turns `alembic check` drift (models vs migrations) into a warning; by default
#                         (1) it fails the smoke
#   SMOKE_SKIP_MCP        1 skips the MCP smoke
set -euo pipefail

RUN_LABEL=smoke
# shellcheck source=scripts/api_server.sh
source "$(dirname "${BASH_SOURCE[0]}")/api_server.sh"

BODY=""
SMOKE_DIAGRAM_ID=""

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

# The gallery migration (0008) runs over an item saved before tags existed: the item must keep
# working, without tags and with its size filled in, and the migration must be reversible.
LEGACY_ITEM_ID="00000000-0000-4000-8000-000000000008"
# Migration 0011 turns the naive deleted_at columns into timestamptz: a workspace soft-deleted before it
# must keep the same instant, read as UTC, also after its downgrade and upgrade. The smoke database runs
# outside UTC, like a server in another time zone, so a conversion in the session time zone would fail.
SMOKE_TIMEZONE="America/Sao_Paulo"
LEGACY_DELETED_WORKSPACE_ID="00000000-0000-4000-8000-000000000011"
LEGACY_DELETED_AT="2026-01-02 03:04:05"

legacy_deleted_at_kept() {
    local deleted_at
    deleted_at="$(sql "SELECT to_char(deleted_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')
                       FROM workspaces WHERE id = '$LEGACY_DELETED_WORKSPACE_ID'")"
    [[ "$deleted_at" == "$LEGACY_DELETED_AT" ]] \
        || fail "the soft-deleted workspace changed its deleted_at: '$deleted_at'"
}

migrate() {
    log "Database time zone set to $SMOKE_TIMEZONE (not UTC)"
    sql "DO \$\$ BEGIN
           EXECUTE format('ALTER DATABASE %I SET timezone = %L', current_database(), '$SMOKE_TIMEZONE');
         END \$\$" > /dev/null \
        || fail "could not set the database time zone"
    local timezone
    timezone="$(sql "SHOW timezone")"
    [[ "$timezone" == "$SMOKE_TIMEZONE" ]] || fail "the database time zone is '$timezone', not $SMOKE_TIMEZONE"
    echo "   ok  new sessions run in $timezone"

    log "alembic upgrade 0007 (clean database), then a gallery item saved before tags existed and a soft-deleted workspace"
    alembic_run upgrade 0007
    sql "INSERT INTO gallery_items (id, owner_id, name, kind, content)
         VALUES ('$LEGACY_ITEM_ID', NULL, 'Legacy item', 'shapes',
                 '{\"shapes\": [{\"id\": \"shape:legacy\"}]}') RETURNING id" > /dev/null \
        || fail "could not seed the legacy gallery item"
    sql "INSERT INTO workspaces (id, name, slug, deleted_at)
         VALUES ('$LEGACY_DELETED_WORKSPACE_ID', 'Legacy deleted', 'smoke-legacy-deleted',
                 '$LEGACY_DELETED_AT') RETURNING id" > /dev/null \
        || fail "could not seed the soft-deleted workspace"

    log "alembic upgrade head (over existing data)"
    alembic_run upgrade head
    local legacy
    legacy="$(sql "SELECT CAST(tags AS text) || ' ' || size_bytes FROM gallery_items WHERE id = '$LEGACY_ITEM_ID'")"
    [[ "$legacy" =~ ^\[\]\ [0-9]+$ ]] || fail "the legacy gallery item was not migrated: '$legacy'"
    echo "   ok  existing gallery item kept, without tags, size filled in"
    legacy_deleted_at_kept
    echo "   ok  existing soft-deleted workspace kept its deleted_at as UTC"

    log "alembic downgrade -1 and upgrade head again (the newest migration is reversible)"
    alembic_run downgrade -1
    alembic_run upgrade head
    legacy_deleted_at_kept
    echo "   ok  soft-deleted workspace kept its deleted_at through the round trip"

    log "alembic check (SQLAlchemy models vs migrations)"
    if DATABASE_URL="$DATABASE_URL" uv run --locked alembic check > "$WORK/check.log" 2>&1; then
        echo "   ok  models match the migrations"
    elif [[ "${SMOKE_STRICT_SCHEMA:-1}" != "0" ]]; then
        cat "$WORK/check.log" >&2
        fail "models and migrations drifted (alembic check)"
    else
        echo "   WARNING: models and migrations drifted (SMOKE_STRICT_SCHEMA=0 keeps the smoke going):"
        grep -E 'Detected|FAILED' "$WORK/check.log" | sed 's/^/     /' || true
    fi
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
    check_soft_delete "$slug" "$@"
}

# deleted_at_is_recent TABLE ID: the row was soft-deleted with the current UTC instant.
deleted_at_is_recent() {
    local found
    found="$(sql "SELECT count(*) FROM $1 WHERE id = '$2'
                  AND deleted_at BETWEEN now() - interval '5 minutes' AND now() + interval '5 minutes'")"
    [[ "$found" == "1" ]] || fail "$1 $2 was not soft-deleted at the current UTC instant"
}

# Soft-deletes a diagram, a folder, a project and a workspace on a throwaway tree: each answers 204,
# disappears from the API and keeps its row with deleted_at set to now.
check_soft_delete() {
    local slug="$1"
    shift
    request POST "$API_URL/workspaces" 201 "{\"name\": \"Smoke delete $slug\", \"slug\": \"smoke-delete-$slug\"}" "$@"
    local workspace_id project_id folder_id diagram_id
    workspace_id="$(json_field "$BODY" id)"
    request POST "$API_URL/workspaces/$workspace_id/projects" 201 '{"name": "Smoke delete"}' "$@"
    project_id="$(json_field "$BODY" id)"
    request POST "$API_URL/projects/$project_id/folders" 201 '{"name": "Smoke delete"}' "$@"
    folder_id="$(json_field "$BODY" id)"
    request POST "$API_URL/projects/$project_id/diagrams" 201 '{"name": "Smoke delete"}' "$@"
    diagram_id="$(json_field "$BODY" id)"

    request DELETE "$API_URL/projects/$project_id/diagrams/$diagram_id" 204 "" "$@"
    request GET "$API_URL/projects/$project_id/diagrams/$diagram_id" 404 "" "$@"
    deleted_at_is_recent diagrams "$diagram_id"
    request DELETE "$API_URL/projects/$project_id/folders/$folder_id" 204 "" "$@"
    request GET "$API_URL/projects/$project_id/folders/$folder_id" 404 "" "$@"
    deleted_at_is_recent folders "$folder_id"
    request DELETE "$API_URL/workspaces/$workspace_id/projects/$project_id" 204 "" "$@"
    request GET "$API_URL/workspaces/$workspace_id/projects/$project_id" 404 "" "$@"
    deleted_at_is_recent projects "$project_id"
    request DELETE "$API_URL/workspaces/$workspace_id" 204 "" "$@"
    request GET "$API_URL/workspaces/$workspace_id" 404 "" "$@"
    deleted_at_is_recent workspaces "$workspace_id"
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
