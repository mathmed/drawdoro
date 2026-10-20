.PHONY: setup dev dev-build run build test test-unit test-mcp test-frontend hooks check-code format-code frontend db \
	smoke smoke-mcp lint-imports mutation mutation-report mutation-changed mcp-manifest \
	suppressions suppressions-update contract contract-prune openapi-diff risk-labels

# Install uv (if missing), project dependencies and git hooks
setup:
	@command -v uv >/dev/null 2>&1 || { \
		echo ">> installing uv"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo ">> uv: $$(uv --version)"
	uv sync
	@[ -f .env ] || { cp .env.example .env && echo ">> created .env from .env.example"; }
	uv run pre-commit install

# Start project in development mode (docker)
dev:
	docker compose --env-file=.env -f ./docker/docker-compose.yaml up

# Start project in development mode with rebuild (docker)
dev-build:
	docker compose --env-file=.env -f ./docker/docker-compose.yaml up --build

# Start only the database (docker)
db:
	docker compose --env-file=.env -f ./docker/docker-compose.yaml up -d --wait db

# Build the production docker image
build:
	docker build --target production -t py-awesome-template -f docker/Dockerfile .

# Start project locally without docker
run:
	uv run uvicorn app.main.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# Run all tests with line and branch coverage (fails under 95%)
test:
	uv run pytest --cov --cov-report=term-missing

# Run only the fast unit tests
test-unit:
	uv run pytest tests/unit

# Run the MCP server tests and type check (separate uv project in mcp/)
test-mcp:
	cd mcp && uv run pytest && uv run mypy .

# Run the frontend lint, type check and tests with coverage (same steps as CI)
test-frontend:
	cd frontend && npm run lint && npm run typecheck && npm run test:coverage

# Run all quality checks (ruff, mypy, import-linter, MCP manifest, suppressions, bandit, vulture,
# xenon, pip-audit)
hooks:
	uv run pre-commit run --all-files

# Regenerate the frontend's list of MCP tools (frontend/src/config/mcpTools.json) from the tools the
# MCP server registers. Run it after adding a tool or changing a tool docstring; the MCP tests fail
# while the file is out of date.
mcp-manifest:
	cd mcp && uv run python manifest.py

# Boot smoke: clean Postgres (throwaway container), alembic upgrade head, real API with auth on and
# off, /health and /ready, then the MCP server against it. Needs docker or SMOKE_DATABASE_URL.
smoke:
	./scripts/smoke.sh

# API contract: clean Postgres + migrations + the real API (auth on, a seeded personal API key) and a
# bounded, deterministic Schemathesis pass against /openapi.json. Fails on any failure that is not in
# contract-baseline.json and on baseline entries that no longer happen. Needs docker or SMOKE_DATABASE_URL.
contract:
	./scripts/contract.sh

# Drop the entries of contract-baseline.json that no longer happen (after a fix); commit the result.
# It never adds an entry: accepting a new failure (`./scripts/contract.sh --baseline-update`) needs the
# owner's approval.
contract-prune:
	./scripts/contract.sh --baseline-prune

# MCP smoke only: streamable-http server, /health, initialize and tools/list
smoke-mcp:
	./scripts/smoke_mcp.sh

# Architecture contracts (import-linter) for the API and the MCP server
lint-imports:
	uv run lint-imports
	cd mcp && uv run lint-imports

# Mutation testing of the use cases and domain services (slow: about 10 minutes). Results are
# cached in mutants/; delete it for a clean run. The report lands in mutants/report.md.
mutation:
	uv run mutmut run
	@$(MAKE) --no-print-directory mutation-report

mutation-report:
	uv run python scripts/mutation.py report > mutants/report.md
	@sed -n '1,4p' mutants/report.md
	@echo ">> full report: mutants/report.md | inspect a mutant: uv run mutmut show <name>"

# Base branch of mutation-changed and openapi-diff
BASE ?= origin/main

# Create (or update) the four risk:<level> labels on the GitHub repository; idempotent, needs gh
risk-labels:
	gh label create "risk:low" --color 0E8A16 --description "Low risk: no behaviour change" --force
	gh label create "risk:medium" --color FBCA04 --description "Medium risk: new behaviour or deploy steps" --force
	gh label create "risk:high" --color D93F0B --description "High risk: can break production or changes behaviour drastically" --force
	gh label create "risk:critical" --color B60205 --description "Critical risk: outage, private data leak or data loss, hard to revert" --force

# Fail on breaking changes between the OpenAPI schema of HEAD (working tree) and of its merge base with
# BASE: oasdiff changelog --fail-on ERR. Needs oasdiff on PATH (see docs/DEVELOPMENT.md).
openapi-diff:
	uv run python scripts/openapi.py diff --base $(BASE)

# What the PR job runs: mutates only the use cases and domain services changed against BASE, down
# to the changed functions, and fails below MUTATION_MIN_SCORE (default 95, the ratchet).
mutation-changed:
	uv run python scripts/mutation.py changed --base $(BASE)

# Suppression ratchet: fails when the noqa, type: ignore, nosec, eslint-disable, @ts-ignore, skipped
# or focused tests... of app/, alembic/, mcp/, scripts/, tests/ and frontend/ differ from
# suppressions-baseline.json, in either direction.
suppressions:
	uv run python scripts/suppressions.py check

# Lower suppressions-baseline.json after removing suppressions. It refuses to raise it: that needs
# `update --allow-increase` and the owner's approval.
suppressions-update:
	uv run python scripts/suppressions.py update

# Lint and check formatting
check-code:
	uv run ruff check . && uv run ruff format --check .

# Fix lint issues and format code
format-code:
	uv run ruff check --fix . && uv run ruff format .

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"
