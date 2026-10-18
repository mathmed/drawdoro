# Shared boot of the real API, sourced by scripts/smoke.sh and scripts/contract.sh (not executable):
# a clean Postgres (a throwaway container, or SMOKE_DATABASE_URL), alembic, uvicorn with .env.example
# plus overrides, and the cleanup that always stops the API and removes the container. On failure it
# prints the API and Postgres logs.
#
# The sourcing script runs with `set -euo pipefail` and sets RUN_LABEL first (smoke, contract): it names
# the container and the failure line `!! <LABEL> FAILED: <reason>` that scripts/quality_report.py reads.
#
# Environment:
#   SMOKE_DATABASE_URL    use this empty database instead of starting a throwaway Postgres container.
#                         It must be clean: migrations run on it.
#   SMOKE_POSTGRES_IMAGE  image of the throwaway container (default: the one in docker-compose.yaml)
#   SMOKE_TIMEOUT         seconds to wait for each process to become ready (default: 60)

RUN_LABEL="${RUN_LABEL:-smoke}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TIMEOUT="${SMOKE_TIMEOUT:-60}"
WORK="$(mktemp -d)"
API_PID=""
API_LOG=""
DB_CONTAINER=""

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
    printf '\n!! %s FAILED: %s\n' "${RUN_LABEL^^}" "$*" >&2
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
    DB_CONTAINER="${APP_SLUG:-app}-${RUN_LABEL}-db-$$"
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

# sql STATEMENT: runs one statement on the database and prints the first column of each row.
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
