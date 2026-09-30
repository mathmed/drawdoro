#!/usr/bin/env bash
# Boot smoke test: migrates a clean Postgres, starts the real API with production-like settings and
# checks it answers. Brand-neutral on purpose: names come from .env.example (APP_SLUG), so the same
# script runs unchanged in every fork.
#
# Modes, in order:
#   production-guard  ENV=production with AUTH_ENABLED=false must refuse to start
#   auth-enabled      ENV=production, AUTH_ENABLED=true (how production runs); also runs the MCP
#                     smoke against this API with the service key
#   auth-disabled     ENV=development, AUTH_ENABLED=false (local development)
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

wait_for() {
    local url="$1" pid="$2" name="$3" deadline=$((SECONDS + TIMEOUT))
    until curl -sf -o /dev/null "$url"; do
        kill -0 "$pid" 2>/dev/null || fail "$name exited before answering $url"
        ((SECONDS < deadline)) || fail "$name did not answer $url within ${TIMEOUT}s"
        sleep 1
    done
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

migrate() {
    log "alembic upgrade head (clean database)"
    DATABASE_URL="$DATABASE_URL" uv run --locked alembic upgrade head > "$WORK/alembic.log" 2>&1 \
        || { cat "$WORK/alembic.log" >&2; fail "alembic upgrade head failed on a clean database"; }
    grep 'Running upgrade' "$WORK/alembic.log" | sed 's/^.*Running upgrade/   applied/' || true

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

# Walks workspace -> project -> diagram -> revision so the newest tables and indexes get used.
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
    request GET "$API_URL/projects/$project_id/tree" 200 "" "$@"
    request GET "$API_URL/projects/$project_id/diagrams" 200 "" "$@"
    request GET "$API_URL/workspaces" 200 "" "$@"
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
if [[ "${SMOKE_SKIP_MCP:-0}" != "1" ]]; then
    SMOKE_MCP_API_URL="$API_URL" SMOKE_MCP_API_KEY="$SERVICE_KEY" "$ROOT/scripts/smoke_mcp.sh" \
        || fail "MCP smoke failed"
fi
stop_api

log "Mode auth-disabled: ENV=development, AUTH_ENABLED=false"
start_api auth-disabled ENV=development AUTH_ENABLED=false
check_probes
check_crud auth-disabled
stop_api

log "Mode database-down: liveness stays up, readiness reports the outage"
start_api database-down ENV=development AUTH_ENABLED=false \
    DATABASE_URL="postgresql+asyncpg://smoke:smoke@127.0.0.1:$(free_port)/smoke"
request GET "$API_URL/health" 200
request GET "$API_URL/ready" 503
stop_api

log "Smoke passed"
