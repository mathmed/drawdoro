# CLAUDE.md

Guidance for AI coding agents in this repository. `AGENTS.md` is a symlink.

## Project

**Drawdoro** is an internal architecture diagramming and documentation tool.

- **Backend**: FastAPI + Python 3.14 (this directory), managed with uv
- **Frontend**: React + Vite + TypeScript in `frontend/`
- **MCP**: Python MCP server in `mcp/`

## Monorepo structure

```
/                  Backend FastAPI API
frontend/          React+Vite+TypeScript frontend
mcp/               Python MCP server
docker/            Dockerfile and docker-compose
```

## Commands

```bash
make setup        install uv, dependencies and git hooks
make run          run the API locally with hot reload
make test         all tests with line and branch coverage (fails under 95%)
make test-unit    only the fast unit tests
make hooks        all quality checks: ruff, mypy, bandit, vulture, xenon, pip-audit
make format-code  fix lint issues and format with ruff
make smoke        boot smoke: clean Postgres + migrations + real API (auth on/off) + MCP
make lint-imports architecture contracts (import-linter) for app/ and mcp/
make mutation     mutation testing of use cases and domain services (slow, weekly in CI)
make mutation-changed  mutation testing of only the domain code changed vs BASE (default origin/main); runs on every PR
```

Always use `uv run` for the backend. Frontend: `cd frontend && npm install && npm run dev`. MCP: `cd mcp && uv run python server.py`.

## Backend architecture rules

```
app/common/        settings and logging, importable by any layer
app/domain/        business core: contracts, entities, usecases, services, errors, enums, constants
app/infra/         implementations of domain contracts
app/presentation/  factories (wiring) and FastAPI routes, middlewares, handlers
app/main/          entry point
tests/unit/        fast tests with mocked dependencies
tests/integration/ HTTP tests with TestClient
```

- `app/domain` never imports from `app/infra`, `app/presentation` or `app/common`.
- Use cases extend `Usecase[Params, Response]`, one public method `execute`.
- Business failures raise errors from `app/domain/errors/`. Never `HTTPException` outside presentation.
- New routes in `presentation/fastapi/routes/` registered in `routes/__init__.py`.
- New env vars in `app/common/settings.py`, `.env.example` and README table.
- Every change comes with tests.

## Domain entities

| Entity | Description |
|---|---|
| Workspace | Group of users; top-level organisational unit |
| Project | Belongs to a Workspace; groups diagrams and folders |
| Folder | Nestable; belongs to a Project or another Folder |
| Diagram | canvas_state (tldraw JSON), semantic_metadata |
| DiagramThumbnail | Preview of a Diagram in one theme (light/dark) for the listing cards, rendered by an editor's browser |
| DocumentationPage | Markdown page linked to a Diagram (one per diagram) |
| Comment | Anchored to a diagram element via element_id |
| CustomShape | tldraw custom shape owned by a user or Workspace |
| GalleryItem | Personal reusable item (tldraw shapes snapshot or image) visible only to its owner |
| User | Member of one or more Workspaces |
| WorkspaceMember | User x Workspace join with role: owner/editor/viewer |

## Before opening a PR (mandatory)

1. The app imports: `uv run python -c "import app.main.main"`.
2. New environment variables have a default or an entry in `.env.example`.
3. `make hooks`, `make test`, `make lint-imports` and `make smoke` pass. A PR with failing checks is not a PR.
4. Existing routes are not removed or renamed unless the task asks for it.
5. The README is updated if the change affects setup, commands, routes, env vars or architecture.

## Validation of agent-generated code

- Run `make smoke` (boots the real API on a clean, migrated Postgres, and the MCP server) and
  `make lint-imports` (architecture contracts) before opening a PR, besides `make hooks` and `make test`.
- Never relax an import-linter contract (`[tool.importlinter]` in `pyproject.toml` or `mcp/pyproject.toml`)
  nor add `ignore_imports` without the owner's approval: fix the import instead.
- Never remove or rename `/health` (liveness) or `/ready` (readiness): deploy probes depend on them.
- Mutation testing runs on every PR (CI job `mutation`, `make mutation-changed` locally): only the use cases
  and domain services changed in the diff, down to the changed functions. The job fails when their score is
  below `MUTATION_MIN_SCORE` (a ratchet, default 95, repository variable). Survivors of the changed code are
  listed in the Quality Report with their diffs: add the missing assertion; never weaken or delete tests,
  shrink `only_mutate` or lower the ratchet to get it green. `make mutation` (whole scope, slow) runs weekly.
  Never commit `mutants/`.
- CI analyses never post comments on their own. Each job runs its tool through
  `scripts/quality_report.py run <analysis> -- <command>` (keeps the exit code: the job stays the gate) and
  uploads `quality-fragment-<job>`; the `quality-report` job builds the single PR comment. A new analysis
  needs an `Analysis` value, an analyzer, a `Check` in `SECTIONS`, the wrapper and artifact in its job, the
  job in the `needs` of `quality-report`, and tests (README, "Quality Report").

## Workflow

- Code changes are delegated to the `coder` agent (`.claude/agents/coder.md`).
- **Exception**: if a `.local_dev` file exists at the root, edit files directly without delegating.
- Use the `reviewer` agent (`.claude/agents/reviewer.md`) to review a branch before merging.

## Personal preferences

Backend Python (`app/` and `mcp/`); the frontend follows its own tooling.

- **Reuse first (YAGNI)**: follow existing patterns. Before creating a function, class, contract, service or
  dependency, reuse what exists. When changing shared code, update every caller.
- **SOLID**: one reason to change per module/class; extend instead of modifying; depend on domain contracts
  received through the constructor, never on `infra` directly.
- **DDD**: invariants, calculations and state transitions live in entities/services in `app/domain`, with no I/O.
  Request/response schemas only carry data and validation.
- **`__init__.py`**: only create when it exports symbols. Never empty.
- **Comments**: no docstrings. Comments only when code is genuinely confusing.
  - Exception: MCP tool functions (`mcp/tools/`) have docstrings, because the MCP SDK sends the docstring to the agent as the tool description. Describe the tool and each parameter (`Args:`).
- **Enums**: always use `enum.StrEnum` for fixed sets of strings.
- **Data structures**: always use `BaseModel` or `dataclass`. Use `dict` only as last resort.
- **Identifiers**: every identifier in English.
- **Language**: all code, comments, logs, docs and user-facing text (including CI reports and step names) in English.
- **Typing**: every parameter and return value is typed. `Any` only if unavoidable.
- **Logging**: never `print`; always `logger = logging.getLogger(__name__)`.
- **Dates**: always timezone-aware UTC: `datetime.now(UTC)`.
- **Edge cases**: list the states, dates and input values that can reach the code and handle each one.
  Irreversible effects (delete, send) happen exactly once.
- **Idempotency**: a repeated call (retry, double click) never duplicates an effect: use an upsert, a unique
  key or a state check.
- **Fail loudly**: never `except Exception: pass`. Catch specific exceptions only where something can be done;
  log unexpected ones with `logger.exception` and propagate or translate them.
- **Nothing internal leaks**: error responses carry no exception text, stack traces, infrastructure names or
  internal details.
- **Hot paths**: no N+1 (query or call inside a loop) and no slow work on paths every request goes through.
- **Early return**: prefer guard clauses over nested ifs.
- **Thin routes**: a route only converts the request, calls the use case and returns response.
- **Public API**: new endpoints require the authenticated user (`dependencies/current_user.py`) unless
  explicitly public, and validate input at the edge. Public contracts only grow additively.
- **Use case names**: start with a verb (CreateUser, ListInvoices), one per file.
- **Tests**: name them `test_should_<behaviour>` and build the SUT in a `sut` fixture.
- **Commits**: Conventional Commits in English: feat, fix, refactor, chore, test, docs, ci, build.
