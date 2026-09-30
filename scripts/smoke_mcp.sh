#!/usr/bin/env bash
# MCP boot smoke test: starts mcp/server.py in streamable-http mode and checks it answers /health,
# the MCP initialize handshake and tools/list, and that it rejects hosts outside its allow-list.
#
# Environment:
#   SMOKE_MCP_API_URL  API the server talks to. When set, a tools/call must also reach it
#                      (scripts/smoke.sh passes the API it started). Unset: an unreachable URL.
#   SMOKE_MCP_API_KEY  key the server sends to the API (MCP_API_KEY)
#   SMOKE_TIMEOUT      seconds to wait for the server to become ready (default: 60)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMEOUT="${SMOKE_TIMEOUT:-60}"
WORK="$(mktemp -d)"
MCP_PID=""
MCP_LOG="$WORK/mcp.log"
BODY=""
# Oldest revision the SDK still negotiates; the server answers with the one it picked.
PROTOCOL_VERSION="2025-06-18"

log() { printf '\n>> %s\n' "$*"; }

fail() {
    printf '\n!! MCP SMOKE FAILED: %s\n' "$*" >&2
    printf '\n----- MCP log -----\n' >&2
    tail -n 200 "$MCP_LOG" >&2 || true
    exit 1
}

cleanup() {
    if [[ -n "$MCP_PID" ]]; then
        kill "$MCP_PID" 2>/dev/null || true
        wait "$MCP_PID" 2>/dev/null || true
    fi
    rm -rf "$WORK"
}
trap cleanup EXIT

free_port() {
    python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])'
}

# rpc EXPECTED_STATUS JSON [CURL_ARGS...]: posts one JSON-RPC message; the reply lands in $BODY.
rpc() {
    local expected="$1" payload="$2"
    shift 2
    local status
    status="$(curl -s -o "$WORK/body" -w '%{http_code}' -X POST "$MCP_URL/mcp" \
        -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
        -H "MCP-Protocol-Version: $PROTOCOL_VERSION" "$@" --data "$payload")" || status="000"
    BODY="$(cat "$WORK/body" 2>/dev/null || true)"
    [[ "$status" == "$expected" ]] \
        || fail "POST /mcp answered $status, expected $expected. Body: ${BODY:0:500}"
}

# Replies may come as plain JSON or as a server-sent event; returns the JSON-RPC message.
message() {
    python3 - "$BODY" <<'PY'
import json
import sys

body = sys.argv[1]
lines = [line[len("data:"):].strip() for line in body.splitlines() if line.startswith("data:")]
print(json.dumps(json.loads(lines[-1] if lines else body)))
PY
}

# assert_message PYTHON_EXPRESSION DESCRIPTION: evaluates the expression on the reply `m`.
assert_message() {
    local parsed
    parsed="$(message)" || fail "unparseable reply: ${BODY:0:500}"
    python3 -c 'import json, sys; m = json.loads(sys.argv[1]); sys.exit(0 if eval(sys.argv[2]) else 1)' \
        "$parsed" "$1" || fail "$2. Reply: ${parsed:0:500}"
    printf '   ok  %s\n' "$2"
}

MCP_PORT="$(free_port)"
MCP_URL="http://127.0.0.1:$MCP_PORT"
API_URL="${SMOKE_MCP_API_URL:-http://127.0.0.1:$(free_port)}"

log "Starting the MCP server (streamable-http) against $API_URL"
(
    cd "$ROOT/mcp"
    exec env MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT="$MCP_PORT" \
        MCP_API_URL="$API_URL" MCP_API_KEY="${SMOKE_MCP_API_KEY:-}" \
        uv run --locked python server.py
) > "$MCP_LOG" 2>&1 &
MCP_PID=$!

deadline=$((SECONDS + TIMEOUT))
until curl -sf -o /dev/null "$MCP_URL/health"; do
    kill -0 "$MCP_PID" 2>/dev/null || fail "the MCP server exited before answering /health"
    ((SECONDS < deadline)) || fail "the MCP server did not answer /health within ${TIMEOUT}s"
    sleep 1
done
echo "   ok  GET /health"

rpc 200 "{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"initialize\", \"params\": {
    \"protocolVersion\": \"$PROTOCOL_VERSION\", \"capabilities\": {},
    \"clientInfo\": {\"name\": \"smoke\", \"version\": \"1\"}}}"
assert_message '"protocolVersion" in m["result"] and m["result"]["serverInfo"]["name"]' \
    "initialize returns the server info"
assert_message '"tools" in m["result"]["capabilities"] and m["result"]["instructions"]' \
    "initialize advertises tools and instructions"

rpc 200 '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
assert_message 'len(m["result"]["tools"]) > 0 and all(t["description"] for t in m["result"]["tools"])' \
    "tools/list returns described tools"
assert_message 'any(t["name"] == "list_workspaces" for t in m["result"]["tools"])' \
    "tools/list includes list_workspaces"

rpc 421 '{"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}' \
    -H 'Host: attacker.example'
echo "   ok  rejects a Host outside the allow-list (421)"

if [[ -n "${SMOKE_MCP_API_URL:-}" ]]; then
    rpc 200 '{"jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "list_workspaces", "arguments": {}}}'
    assert_message '"result" in m and not m["result"].get("isError")' \
        "tools/call list_workspaces reaches the API"
fi

log "MCP smoke passed"
