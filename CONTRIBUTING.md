# Contributing to Drawdoro

Thanks for helping! Every change comes with tests, and the checks are never loosened to let code through.
[`CLAUDE.md`](CLAUDE.md) holds the full rules (architecture, conventions, style) that people and AI agents follow
alike; [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) explains how the pieces fit and
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) lists every command and quality gate. Report security problems
privately, as [`SECURITY.md`](SECURITY.md) explains.

## Running it locally

You need [uv](https://docs.astral.sh/uv/) (Python 3.14 is pinned in `.python-version`), Node.js 22 or newer for
the frontend, and Docker for the database and the boot smoke.

```sh
make setup        # uv, dependencies, git hooks (pre-commit) and a .env from .env.example
make db           # Postgres only, in Docker
make run          # the API at http://localhost:8000
cd frontend && npm install && npm run dev   # the frontend at http://localhost:3000
```

Always use `uv run` for the backend. The MCP server is a separate uv project in `mcp/`; see
[`docs/MCP.md`](docs/MCP.md).

## Making a change

1. Branch from `main`; one pull request, one subject.
2. Respect the layers: domain (contract, use case) → infra (implementation) → presentation (factory, route).
   [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#adding-a-feature) has the steps of a new feature.
3. Write the tests: unit tests in `tests/unit/` mirroring `app/`, route tests in `tests/integration/`, MCP tests in
   `mcp/tests/`, frontend tests next to the code as `*.test.ts(x)`. Mock the external dependencies (databases,
   HTTP, third-party APIs).
4. Run the checks before opening the pull request:
   - `uv run python -c "import app.main.main"` (the app imports);
   - `make hooks` (ruff, mypy, bandit, vulture, xenon, pip-audit, import-linter, MCP manifest, suppression ratchet);
   - `make test` (line and branch coverage, fails under 95%);
   - `make lint-imports` (architecture contracts of the API and the MCP server);
   - `make smoke` (clean Postgres, migrations, the real API with auth on and off, and the MCP server);
   - `make contract` (Schemathesis against the real API; new failures fail, see
     [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md#api-contract-schemathesis));
   - `make mutation-changed` when you touch `app/domain/usecases/` or `app/domain/services/`;
   - `make test-mcp` for `mcp/`, and `make test-frontend` plus `npm run build` for `frontend/`.
5. Commit with [Conventional Commits](https://www.conventionalcommits.org/) in English (`feat`, `fix`,
   `refactor`, `chore`, `test`, `docs`, `ci`, `build`).
6. Open the pull request against `main` with a *What*, *Why* and *How to test* section. CI posts one
   **Quality Report** comment ([`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md#quality-report)); a failing check means
   it is not ready.

## Rules that are easy to miss

- New environment variables go into `app/common/settings.py`, `.env.example` and
  [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md), with a default when possible.
- Existing routes are not removed or renamed unless that is the point of the change; never remove or rename
  `/health` and `/ready`, which deploy probes depend on. Public contracts only grow additively.
- Never relax an import-linter contract, add `ignore_imports`, lower a coverage or mutation threshold, or add a
  suppression to get a pull request green: fix the code instead. Relaxing a gate needs the owner's approval. The
  suppression ratchet (`make suppressions`) fails on any new `# noqa`, `eslint-disable`, `@ts-ignore`, skipped
  test...; after removing some, commit the lower baseline with `make suppressions-update`.
- Keep code identifiers brand-neutral: everything people or agents read takes the product name from
  configuration, so forks merge upstream cleanly ([`docs/WHITE_LABEL.md`](docs/WHITE_LABEL.md)).
- Update the README or the relevant file in `docs/` when the change affects setup, commands, routes, environment
  variables or architecture.
- Never commit `mutants/`.

Dependabot proposes grouped weekly updates of the Python dependencies and the GitHub Actions after a cooldown.
