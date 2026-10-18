#!/usr/bin/env bash
# API contract test: migrates a clean Postgres, starts the real API the way production runs it
# (ENV=production, AUTH_ENABLED=true) and runs a bounded, deterministic Schemathesis pass against its
# OpenAPI schema (/openapi.json). Every response must match the documented status codes, content types,
# headers and schemas, invalid input must be rejected and nothing may answer with a 5xx.
#
# What it exercises: every HTTP operation of /openapi.json, as a seeded user with a personal API key
# (X-API-Key), the identity agents use, so the user's own gallery and workspace roles apply. No identity
# provider is called and nothing outside the throwaway database is touched.
# What it leaves out:
#   - the WebSockets (/ws/...): they are not in the OpenAPI schema; the frontend and unit tests cover them;
#   - the `ignored_auth` check: agents authenticate with the X-API-Key header, which the schema declares as
#     a parameter rather than a security scheme, so Schemathesis would read every accepted request as
#     "authentication ignored". The smoke checks 401 without credentials and with a wrong key.
#
# Known failures live in contract-baseline.json (Schemathesis' own baseline): they are still exercised and
# reported, but only a failure that is not in it fails the run. An entry that no longer reproduces fails it
# too, so a fix locks itself in: run `make contract-prune` and commit the smaller baseline in the same PR.
# Accepting a new failure (`./scripts/contract.sh --baseline-update`) needs the owner's approval.
#
# The boot (Postgres, alembic, uvicorn, cleanup) lives in scripts/api_server.sh, shared with
# scripts/smoke.sh; its header lists SMOKE_DATABASE_URL, SMOKE_POSTGRES_IMAGE and SMOKE_TIMEOUT.
#
# Environment, besides those:
#   CONTRACT_MAX_EXAMPLES     test cases generated per operation and phase      (default 25)
#   CONTRACT_SEED             seed of the data generation                       (default 1)
#   CONTRACT_REQUEST_TIMEOUT  seconds before a single request counts as failed  (default 5)
#
# Extra arguments go straight to `schemathesis run` (e.g. --baseline-prune, --include-path ...).
set -euo pipefail

RUN_LABEL=contract
# shellcheck source=scripts/api_server.sh
source "$(dirname "${BASH_SOURCE[0]}")/api_server.sh"

MAX_EXAMPLES="${CONTRACT_MAX_EXAMPLES:-25}"
SEED="${CONTRACT_SEED:-1}"
REQUEST_TIMEOUT="${CONTRACT_REQUEST_TIMEOUT:-5}"
BASELINE="$ROOT/contract-baseline.json"

# Prints the secret of a new personal API key of a seeded user, hashed with the API's own code.
seed_personal_key() {
    uv run --locked python - <<'PY'
import asyncio
import os
import uuid

import asyncpg

from app.domain.constants.api_keys import API_KEY_VISIBLE_CHARS
from app.domain.services.api_key_secret import generate_api_key_secret, hash_api_key_secret


async def main() -> None:
    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    secret = generate_api_key_secret()
    connection = await asyncpg.connect(url)
    try:
        user_id = await connection.fetchval(
            "INSERT INTO users (id, name, email) VALUES ($1, 'Contract', 'contract@example.com')"
            " RETURNING id",
            uuid.uuid4(),
        )
        await connection.execute(
            "INSERT INTO api_keys (id, user_id, label, prefix, key_hash)"
            " VALUES ($1, $2, 'contract', $3, $4)",
            uuid.uuid4(),
            user_id,
            secret[:API_KEY_VISIBLE_CHARS],
            hash_api_key_secret(secret),
        )
    finally:
        await connection.close()
    print(secret)


asyncio.run(main())
PY
}

load_env_example
start_database
export DATABASE_URL

log "alembic upgrade head (clean database)"
alembic_run upgrade head

log "Seeding a user with a personal API key"
API_KEY="$(seed_personal_key)" || fail "could not seed the personal API key"
echo "   ok  personal key ready"

start_api production ENV=production AUTH_ENABLED=true \
    SERVICE_API_KEY="contract-$(python3 -c 'import secrets; print(secrets.token_hex(16))')" \
    COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID:-us-east-1_contract}" \
    COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID:-contract-client}"

log "Schemathesis against /openapi.json (seed $SEED, up to $MAX_EXAMPLES examples per operation and phase)"
# One worker, a fixed seed, no example database and every example run even after a failure: the same
# code against a clean database always sends the same requests, so a CI failure reproduces locally with
# `make contract` (change CONTRACT_SEED to explore other inputs). The run happens in $WORK, so the
# Hypothesis and Schemathesis caches never land in the repository.
status=0
(cd "$WORK" && uv run --project "$ROOT" --locked schemathesis run "$API_URL/openapi.json" \
    --checks all \
    --exclude-checks ignored_auth \
    --header "X-API-Key: $API_KEY" \
    --workers 1 \
    --seed "$SEED" \
    --generation-database none \
    --continue-on-failure \
    --max-examples "$MAX_EXAMPLES" \
    --request-timeout "$REQUEST_TIMEOUT" \
    --baseline "$BASELINE" \
    --no-color \
    "$@") 2>&1 | tee "$WORK/schemathesis.log" || status=$?

if ((status != 0)); then
    fail "schemathesis found failures that are not in contract-baseline.json (or could not run), see above"
fi
if grep -q "Unobserved entries:" "$WORK/schemathesis.log"; then
    fail "contract-baseline.json lists failures that no longer happen: run \`make contract-prune\` and commit it"
fi

log "Contract passed"
