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
make test         all tests with coverage (fails under 80%)
make test-unit    only the fast unit tests
make hooks        all quality checks: ruff, mypy, bandit, vulture, xenon, pip-audit
make format-code  fix lint issues and format with ruff
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
| Diagram | canvas_state (tldraw JSON), mermaid_source, d2_source, semantic_metadata |
| DocumentationPage | Markdown page linked to a Diagram (one per diagram) |
| Comment | Anchored to a diagram element via element_id |
| Template | Reusable diagram global or scoped to a Workspace |
| CustomShape | tldraw custom shape owned by a user or Workspace |
| ADR | Architecture Decision Record: proposed/accepted/deprecated/superseded |
| User | Member of one or more Workspaces |
| WorkspaceMember | User x Workspace join with role: owner/editor/viewer |

## Before opening a PR (mandatory)

1. The app imports: `uv run python -c "import app.main.main"`.
2. New environment variables have a default or an entry in `.env.example`.
3. `make hooks` and `make test` pass. A PR with failing checks is not a PR.
4. Existing routes are not removed or renamed unless the task asks for it.
5. The README is updated if the change affects setup, commands, routes, env vars or architecture.

## Workflow

- Code changes are delegated to the `coder` agent (`.claude/agents/coder.md`).
- **Exception**: if a `.local_dev` file exists at the root, edit files directly without delegating.
- Use the `reviewer` agent (`.claude/agents/reviewer.md`) to review a branch before merging.

## Personal preferences

- **`__init__.py`**: only create when it exports symbols. Never empty.
- **Comments**: no docstrings. Comments only when code is genuinely confusing.
- **Enums**: always use `enum.StrEnum` for fixed sets of strings.
- **Data structures**: always use `BaseModel` or `dataclass`. Use `dict` only as last resort.
- **Identifiers**: every identifier in English.
- **Typing**: every parameter and return value is typed. `Any` only if unavoidable.
- **Logging**: never `print`; always `logger = logging.getLogger(__name__)`.
- **Dates**: always timezone-aware UTC: `datetime.now(UTC)`.
- **Thin routes**: a route only converts the request, calls the use case and returns response.
- **Use case names**: start with a verb (CreateUser, ListInvoices), one per file.
- **Exceptions**: never `except Exception: pass`. Catch specific exceptions.
- **Early return**: prefer guard clauses over nested ifs.
- **Tests**: name them `test_should_<behaviour>` and build the SUT in a `sut` fixture.
- **Commits**: Conventional Commits in English: feat, fix, refactor, chore, test, docs, ci, build.
