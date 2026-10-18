# Development

How to run Drawdoro locally, the Make targets, the frontend checks and conventions, and the quality gates every
pull request goes through. [`CONTRIBUTING.md`](../CONTRIBUTING.md) has the workflow of a change;
[`CLAUDE.md`](../CLAUDE.md) the full rules.

## Running locally

```sh
make setup     install uv, dependencies and git hooks
make run       start the API at http://localhost:8000
```

Frontend (separate terminal), with Node.js 22 or newer:

```sh
cd frontend
npm install
npm run dev    starts at http://localhost:3000
```

Or run everything with Docker (API, frontend, MCP server and Postgres):

```sh
make dev
```

`make db` starts only Postgres; `uv run alembic upgrade head` applies the migrations to it (`make migrate` runs
`alembic upgrade head` directly, so it needs the project's virtual environment active). Always use `uv run` for the backend.
The MCP server alone runs with `cd mcp && uv run python server.py` (see [MCP server](MCP.md)).

Health checks: `curl http://localhost:8000/health` (liveness, never touches the database) and
`curl http://localhost:8000/ready` (readiness: `503` while the database is unreachable).

## Make targets

| Command | Description |
|---|---|
| `make setup` | Install uv, project dependencies and git hooks |
| `make run` | Run the API locally with hot reload |
| `make dev` | Run all services with Docker |
| `make db` | Start only the Postgres database with Docker (detached, waits for healthcheck) |
| `make build` | Build the production Docker image |
| `make test` | Run all tests with coverage |
| `make test-unit` | Run only the unit tests |
| `make test-mcp` | Run the MCP server tests and type check |
| `make test-frontend` | Run the frontend lint, type check and tests with coverage |
| `make hooks` | Run all quality checks (ruff, mypy, import-linter, MCP manifest, suppression ratchet, bandit, vulture, xenon, pip-audit) |
| `make format-code` | Fix lint issues and format the code |
| `make smoke` | Boot smoke: clean Postgres, `alembic upgrade head`, real API (auth on and off), `/health`, `/ready` and the MCP server. See [Boot smoke](#boot-smoke) |
| `make smoke-mcp` | MCP smoke only: streamable-http server, `/health`, `initialize` and `tools/list` |
| `make contract` | API contract: clean Postgres, migrations, the real API with auth on and a bounded, deterministic Schemathesis pass against `/openapi.json`. See [API contract](#api-contract-schemathesis) |
| `make contract-prune` | Drop the entries of `contract-baseline.json` that no longer happen, after a fix (never adds one) |
| `make openapi-diff` | Fail on breaking changes between the OpenAPI schema of the working tree and of its merge base with `BASE` (default `origin/main`). Needs `oasdiff`, see [Breaking API changes](#breaking-api-changes-oasdiff) |
| `make lint-imports` | Check the architecture contracts (import-linter) of the API and the MCP server |
| `make mutation` | Mutation testing (mutmut) of the use cases and domain services; report in `mutants/report.md` |
| `make mcp-manifest` | Regenerate `frontend/src/config/mcpTools.json` (the *Available tools* list in *Connect Claude*) from the tools the MCP server registers. The MCP tests and a pre-commit hook fail while it is out of date |
| `make suppressions` | Suppression ratchet: fails when the suppressions of the repository differ from `suppressions-baseline.json`. See [Suppression ratchet](#suppression-ratchet) |
| `make suppressions-update` | Lower `suppressions-baseline.json` after removing suppressions (never raises it) |
| `make mutation-changed` | What the PR job runs: mutation testing of only the use cases and domain services changed against `BASE` (default `origin/main`) |
| `make risk-floor` | Minimum risk level of the commits of `REF` (default `HEAD`) against `BASE`, from `.github/risk-floors.yaml`. See [Pull requests and risk](#pull-requests-and-risk) |
| `make risk-labels` | Create or update the four `risk:<level>` labels on the GitHub repository (idempotent, needs `gh`) |
| `make migrate` | Apply database migrations (requires running DB) |
| `make migration msg="desc"` | Generate a new Alembic migration |

## Frontend

### Checks

The frontend needs Node.js 22 or newer. From `frontend/`:

| Command | Description |
|---|---|
| `npm run lint` | ESLint (`eslint.config.js`): TypeScript, React Hooks and React Refresh rules; fails on any warning (`--max-warnings 0`) |
| `npm run typecheck` | `tsc --noEmit` over `src/`, tests included |
| `npm test` | Vitest + React Testing Library on jsdom, once |
| `npm run test:watch` | Vitest in watch mode |
| `npm run test:coverage` | Tests with V8 coverage; the report goes to `frontend/coverage/` |
| `npm run build` | Type check and production build |

Tests live next to the code as `*.test.ts(x)`; shared helpers are in `src/test/`. They cover the pure and critical
modules (branding, auth session, Zustand stores, formatting and validation utilities), simple components and the
loading states of the main screens; the tldraw canvas is not unit tested. Tests always run with
`VITE_APP_NAME=Test App` (set in `vitest.config.ts`), so they never depend on the product name or on a local `.env`.

Coverage thresholds (`vitest.config.ts`) fail the run when coverage drops: a low global floor (10%; about 40% is
covered today, since the canvas and several views are untested) and stricter per-file floors for the covered modules
(90% for the auth session, branding and utilities; 60% for the stores). Raise them as tests are added.

CI runs the `frontend` job on every pull request and on pushes to `main`: `npm ci`, lint, type check, tests with
coverage and `vite build`.

### Loading states

Every wait uses the primitives in `frontend/src/components/ui/loading/` (CSS in `src/styles/loading.css`, no
animation library):

| Primitive | Use it for |
|---|---|
| `BrandLoader` | Full-area waits (session check, sign-in, opening a diagram or a shared link): the product logo with a soft halo, an orbiting arc and a sheen, a label, and after 8 s a "taking longer than usual" hint with an optional retry |
| `LoadingOverlay` | Covers an area with a loader while the content mounts underneath, then fades out (`screen` for the whole viewport) |
| `LoadingGate` | Swaps content for a fallback (usually a skeleton), with an optional `placeholder` that reserves the room during the delay |
| `Skeleton`, `SkeletonGroup`, `ListSkeleton` | Placeholders with a shimmer that mirror the real layout (sidebar rows, diagram cards, gallery tiles, lists), so nothing moves when the data arrives |
| `Spinner` | Pending buttons and small areas; set `aria-busy` on the busy element |
| `TopProgressBar` | Work that keeps the current content on screen (switching diagrams, refreshing a project) |
| `CanvasLoadingScreen` | tldraw's `LoadingScreen` slot; takes over seamlessly from a loader already on screen |

`useDelayedVisibility` (in `src/hooks/`) drives them: a loader appears only after 180 ms, so fast loads never flash
one, and once shown it stays at least 450 ms, so it never flickers. Loaders announce themselves with `role="status"`,
the decorative blocks are `aria-hidden`, and with `prefers-reduced-motion` every movement becomes a slow fade. The
loaders are branded through configuration, see [White-label](WHITE_LABEL.md).

## Validation of agent-generated code

Deterministic checks catch what unit tests with mocks miss: the boot smoke, the API contract, the architecture
contracts, the suppression ratchet and mutation testing. Agents run `make smoke`, `make contract` and
`make lint-imports` before opening a PR (see `CLAUDE.md`). Their results, with every other CI analysis, land in a
single [Quality Report](#quality-report) comment on the PR.

### Boot smoke

`make smoke`, CI job `smoke`. `scripts/smoke.sh` starts a throwaway Postgres container (same image as
`docker-compose.yaml`, no volume, so it is always empty), sets its time zone to `America/Sao_Paulo` (not UTC, like a
server in another time zone), migrates it up to revision `0007`, seeds a gallery item and a soft-deleted workspace,
runs `alembic upgrade head` over it (then downgrades and upgrades the newest migration again; the soft-deleted
workspace keeps its `deleted_at` as UTC throughout) and starts the real API with `.env.example` plus these modes:

| Mode | Settings | Checks |
|---|---|---|
| production-guard | `ENV=production`, `AUTH_ENABLED=false` | the API refuses to start |
| auth-enabled | `ENV=production`, `AUTH_ENABLED=true`, a random `SERVICE_API_KEY` | `/health`, `/ready`, `/openapi.json`; `401` without credentials; workspace → project → diagram → revision with the service key, then soft-deletes a diagram, folder, project and workspace (`204`, gone from the API, `deleted_at` set to now in UTC); the service key gets `403` on the gallery; then the MCP smoke against this API |
| auth-disabled | `ENV=development`, `AUTH_ENABLED=false` | the same probes and CRUD walk; gallery tags, search and an insertion next to a shape; then the MCP smoke on the gallery tools |
| database-down | database URL pointing to a closed port | `/health` stays `200`, `/ready` answers `503` |

It also runs `alembic check` (models versus migrations) and fails on drift; set `SMOKE_STRICT_SCHEMA=0`
to only print a warning while working on a migration. On any failure it prints the API and Postgres logs, and it
always removes the container and stops the processes.

`scripts/smoke_mcp.sh` (`make smoke-mcp`) starts `mcp/server.py` in streamable-http mode and checks
`/health`, the MCP `initialize` handshake, `tools/list`, that a foreign `Host` is rejected (`421`) and,
when given an API, that `tools/call list_workspaces` reaches it. With `SMOKE_MCP_GALLERY=service` it checks that
the gallery tools explain the service key has no gallery; with `personal`, it lists, describes, inserts and tags
gallery items and reads the diagram and its history back.

| Variable | Default | Description |
|---|---|---|
| `SMOKE_DATABASE_URL` | - | Use this **empty** database instead of starting a container (no docker needed) |
| `SMOKE_POSTGRES_IMAGE` | image of `db` in `docker-compose.yaml` | Postgres image of the throwaway container |
| `SMOKE_TIMEOUT` | `60` | Seconds to wait for Postgres, the API and the MCP server |
| `SMOKE_STRICT_SCHEMA` | `1` | `0` turns `alembic check` drift into a warning instead of failing the smoke |
| `SMOKE_SKIP_MCP` | `0` | `1` skips the MCP smoke inside `make smoke` |

The boot itself (throwaway Postgres, alembic, uvicorn, cleanup and logs on failure) lives in
`scripts/api_server.sh`, which `scripts/smoke.sh` and `scripts/contract.sh` source.

### API contract (Schemathesis)

`make contract`, CI job `contract`. `scripts/contract.sh` boots the API like the smoke (throwaway Postgres,
`alembic upgrade head`, `.env.example`), seeds a user with a personal API key and starts the API the way
production runs it (`ENV=production`, `AUTH_ENABLED=true`). Then [Schemathesis](https://schemathesis.readthedocs.io/)
reads `/openapi.json` and runs every check (`--checks all`) on every HTTP operation, as that user (`X-API-Key`):
documented status codes, content types, headers and response schemas, invalid input rejected, valid input
accepted, no 5xx, and the stateful phase that chains operations through the links it infers.

It is **bounded and deterministic**: one worker, a fixed seed (`CONTRACT_SEED`, default 1), up to
`CONTRACT_MAX_EXAMPLES` (default 25) generated cases per operation and phase, no example database, every example
run even after a failure, a 5 s request timeout (`CONTRACT_REQUEST_TIMEOUT`) and always a clean database, so the
same code sends the same requests and a CI failure reproduces locally. It takes about a minute and a half.

What it leaves out, on purpose:

- the WebSockets (`/ws/diagrams/{id}`, `/ws/workspaces/{id}/presence`): they are not part of the OpenAPI schema;
- the identity provider: no Cognito token is involved. The seeded personal key is the identity agents use, so
  the user's own gallery and workspace roles apply; managing personal keys (`/me/api-keys`) only works from a
  browser session, so there it only sees the `403`;
- the `ignored_auth` check: agents send the key in the `X-API-Key` header, which the schema declares as a parameter
  rather than a security scheme, so Schemathesis would take every accepted request for "authentication ignored".
  The smoke checks the `401` without credentials and with a wrong key.

**Known failures** live in `contract-baseline.json`, Schemathesis' own
[baseline](https://schemathesis.readthedocs.io/): each entry is an operation, a check and the signature of the
failure (for example `POST /workspaces`, `not_a_server_error`, `500`). They are still exercised and listed as known,
but only a failure that is not in the file fails the run. The first run recorded the API as it was: undocumented
status codes (mostly `404`), naive timestamps that are not RFC 3339 `date-time`, domain `422` errors whose `detail`
is a string instead of the documented list, missing `Allow` headers on `405`, and `500`s on unknown parents, a
duplicate workspace slug or NUL bytes in text (those `500`s have since been fixed). It works as a ratchet:

- a **new failure** fails the job: fix the route or document the response (`responses=` on the route). Accepting
  it (`./scripts/contract.sh --baseline-update`) needs the owner's explicit approval;
- an entry that **no longer happens** fails it too, so a fix locks itself in: run `make contract-prune` and commit
  the smaller baseline in the same PR.

Extra arguments of `scripts/contract.sh` go to `schemathesis run` (for example `--include-path /workspaces` while
fixing one route). On a merge conflict in `contract-baseline.json`, take either side and rerun `make contract`:
it says what is new and what to prune.

### Breaking API changes (oasdiff)

`make openapi-diff`, CI job `openapi-diff` (pull requests only). `scripts/openapi.py diff` exports the OpenAPI
schema of the working tree and of its merge base with the base branch (checked out in a temporary `git worktree`,
with its own environment of production dependencies) and runs
[oasdiff](https://github.com/oasdiff/oasdiff) `changelog --fail-on ERR`: removing or renaming a route, removing a
response field, making a parameter required or narrowing a type fails the PR. Warnings (possible breaking changes)
show as ⚠️ in the Quality Report without failing; additive changes are listed as information. Both exports run
from a temporary directory, so a local `.env` never makes the two schemas differ.

Public contracts only grow additively (`CLAUDE.md`): a deliberate breaking change needs the owner's explicit
approval and is called out in the PR. Locally, install the same version CI pins in `ci.yml` (`OASDIFF_VERSION`):
`go install github.com/oasdiff/oasdiff@v1.33.0`, or the `oasdiff_<version>_linux_amd64.tar.gz` /
`darwin_all.tar.gz` binary of its [release](https://github.com/oasdiff/oasdiff/releases) on your `PATH`. CI
downloads it and checks its sha256; Dependabot does not track it, so bump `OASDIFF_VERSION` and `OASDIFF_SHA256`
together.

### Static analysis thresholds

`make hooks`, CI jobs `lint` and `quality`. The backend holds the strictest setting of every tool, with no
per-file ignore or vulture allowlist. A regression fails pre-commit and CI.

The few line-scoped suppressions left are counted by the [suppression ratchet](#suppression-ratchet) and listed in
`suppressions-baseline.json`. Most are `# nosec` in `scripts/`, where running a process is the job: `B404`
(importing `subprocess`) and `B603` (a process started without a shell) in `quality_report.py`
(`run <analysis> -- <command>` runs the CI analysis commands), `mutation.py` (`git` and `mutmut`) and
`openapi.py` (`git`, `uv` and `oasdiff`), the last two resolving the executables to absolute paths with
`shutil.which`. Bandit flags every `subprocess` call at low severity whatever its
input, so these are reviewed call sites, not tolerated findings; nothing else may be suppressed without the
owner's approval.

| Tool | Scope | Threshold |
|---|---|---|
| ruff (lint + format) | whole repository | zero findings (`E`, `F`, `I`, `UP`, `B`, `SIM`) |
| mypy | `app`, `tests`, `scripts`; `mcp/` | `strict = true`, zero errors |
| bandit | `app`, `mcp/`, `scripts/` (not `mcp/tests`) | zero findings at **every** severity (no `-ll`) |
| vulture | `app` | zero findings at confidence 80, **blocking** (no longer advisory) |
| xenon | `app`, `mcp/`, `scripts/` (not `mcp/tests`) | rank **A** absolute, per module and on average (`--max-absolute A --max-modules A --max-average A`) |
| import-linter | `app`, `mcp/` | every contract, no `ignore_imports` |
| coverage | `app` | line **and** branch coverage, `fail_under = 95` (ratchet, baseline 95.7%) |
| mutmut | use cases and domain services | `MUTATION_MIN_SCORE` ratchet, see below |

Thresholds are ratchets: raise them when the code allows it, never lower them to get a PR green.

### Suppression ratchet

`make suppressions`, pre-commit hook `suppressions` and a step of the CI job `lint`. `scripts/suppressions.py`
counts, per file and per kind, every suppression in `app/`, `alembic/`, `mcp/`, `scripts/`, `tests/` and
`frontend/` (skipping hidden directories such as `.venv`, `node_modules`, `dist`, `coverage` and caches) and
compares the counts with the committed `suppressions-baseline.json`:

| Language | What counts |
|---|---|
| Python | `# noqa`, `# type: ignore`, `# nosec`, `# pragma: no cover` / `no branch`, `# pylint: disable`, `# mypy:`, `# pyright:`, `# fmt: off` / `skip` (and `isort`/`yapf`), `pytest.mark.skip` / `skipif` / `xfail`, `pytest.skip()` / `xfail()` / `importorskip()`, `unittest.skip*` / `expectedFailure`, `self.skipTest()` |
| TypeScript / JavaScript | `eslint-disable` (also `-line`, `-next-line` and inline rule configuration such as `/* eslint no-console: "off" */`), `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`, `istanbul` / `v8` / `c8 ignore`, `prettier-ignore`, skipped tests (`it` / `test` / `describe` / `suite` `.skip`, `.skipIf`, `.runIf`, `.todo`, `xit`, `xdescribe`, `ctx.skip()`), focused tests (`.only`, `fit`, `fdescribe`) and expected failures (`.fails`) |

Python comments are read with the tokenizer and test markers with the AST, so the same words inside strings do
not count. In TypeScript a directive only counts right after a comment opener (`//`, `/*`).

Any difference fails, in both directions:

- **more** suppressions in a file than in the baseline: remove them and fix the cause. Raising the baseline
  (`uv run python scripts/suppressions.py update --allow-increase`) needs the owner's explicit approval and is
  called out in the PR;
- **fewer**: lock the improvement in with `make suppressions-update` and commit the lower baseline in the same
  PR. The target refuses to raise any count.

Moving a suppression to another file counts as one more there and one less in the old file. The Quality Report
shows the totals by kind, or the files and lines that changed.

### Architecture contracts

`make lint-imports`. The import-linter contracts of the API and the MCP server, and the rule that they hold with no
`ignore_imports`, are described in [Architecture](ARCHITECTURE.md#architecture-contracts).

### Mutation testing

`make mutation-changed` on PRs, `make mutation` weekly. [mutmut](https://mutmut.readthedocs.io/) changes the code
one small edit at a time (a `<` becomes `<=`, an argument becomes `None`...) and runs the unit tests against each
change. The scope is `only_mutate` in `[tool.mutmut]` of `pyproject.toml`: `app/domain/usecases/` and
`app/domain/services/`.

- **On every PR** (CI job `mutation`, `make mutation-changed` locally): `scripts/mutation.py changed` diffs
  the branch against the base, keeps the files in scope and maps the changed lines to the functions and
  methods that contain them, so only their mutants run. A change outside any function (a constant, a class
  attribute) mutates the whole file; imports, blank lines and comments are ignored. The job fails when the
  score of what it mutated is below `MUTATION_MIN_SCORE`, and the Quality Report lists the survivors of the
  changed code with their diffs. It has a 20-minute timeout and caches `mutants/`.
- **Weekly** (*Mutation testing* workflow, Mondays 06:00 UTC, and on demand with `workflow_dispatch` and an
  optional minimum score): mutates the whole scope (about 2,700 mutants, 5 to 10 minutes locally) and publishes the
  per-package and per-file report in the job summary and the `mutation-report` artifact. It never gates.

`MUTATION_MIN_SCORE` is a **ratchet**: a floor a bit below the current baseline, 95 by default. The first
full run scored 67.7% (ratchet 60); the whole scope now scores 100% (2,704 mutants) with no surviving mutant, and the
floor stays a little below 100% because the PR job scores only the few functions a change touches, where a
single mutant that no test can tell apart (an equivalent mutant) weighs a lot. It only goes up: raise it as tests
improve, in the repository variable `MUTATION_MIN_SCORE` (Settings → Secrets and variables → Actions → Variables)
or the default in `scripts/mutation.py` and `ci.yml`. To change what is mutated, edit `only_mutate`; both runs
follow it.

Reading the result (`mutants/report.md` locally, job summary and `mutation-report` artifact in CI):

- **killed**: a test failed, so the tests pin that behaviour down (timeouts count as killed);
- **survived**: every test still passed, so nothing checks that line; `uv run mutmut show <name>` prints the diff;
- **no tests**: no unit test runs that code at all (counts as not killed);
- **score** = killed / all mutants. Survivors that only change an error message are usually noise; survivors
  that change a comparison, a condition or the id passed to a repository are real gaps.

Results are cached in `mutants/` (git-ignored): the next run only re-tests what changed. Delete it for a
clean run; `uv run mutmut browse` explores the results interactively.

### Pull requests and risk

Every pull request description follows [`.github/pull_request_template.md`](../.github/pull_request_template.md):

| Section | What goes in it |
|---|---|
| **Risk** | `low`, `medium`, `high` or `critical` and one line of why |
| **Summary** | One sentence: what changes in behavior, and why |
| **Behavior** | Up to five changes, most critical first, as *before → after*, in plain words for someone who has not read the code: no backticks, paths, file, function or test names |
| **Unchanged** | What a reviewer might fear broke, or "behavior-preserving refactor" |
| **Look here** | The only place for file, function and test references: the evidence (test or code) of every Behavior item, pipeline or check changes, departures from the task and what deserves a human look |
| **Deploy steps** | Always present: env vars, secrets, migration order, flags, external configuration, rollback; or "None: normal merge and deploy." |
| **Not verified** | What the author could not check, or "nothing"; plus **Mismatch** when the diff contradicts the author's handoff notes |

The risk level has floors by file, in [`.github/risk-floors.yaml`](../.github/risk-floors.yaml): pipeline config
(dependency manifests and locks, pre-commit, `Makefile`, baselines, `scripts/`, `.github/`, `.claude/`,
`CLAUDE.md`, `docker/`, the frontend's build, lint, test and TypeScript configuration), database migrations (and
the SQLAlchemy models) and auth (sign-in, API keys, share tokens, workspace roles, the dependencies that decide who
may do what, the settings) are never below **high**, and any deploy step other than "None" makes it at least
**medium**. `make risk-floor` prints the floor of the current branch and the files that set it.

The *Risk label* workflow (`.github/workflows/risk-label.yml`, outside `ci.yml` so a label change does not rerun
every analysis) requires exactly one `risk:<level>` label on the PR and fails when it is below the file floor
(`scripts/risk.py`). It reruns when labels change. Dependabot PRs get `risk:high`, since they change
pipeline config. Create the labels once with `make risk-labels`.

### Quality Report

Every PR gets **one** comment titled *Quality Report* (found and updated through the
`<!-- quality-report -->` marker), rebuilt on each push by the `quality-report` job:

- the top line is the verdict (❌ failed, ⚠️ passed with warnings, ✅ all good) and the table has one row per
  analysis: backend lint/format, types (API and MCP), security, dead code, complexity, tests and coverage
  (API and MCP), architecture contracts (API and MCP), boot smoke, mutation testing, the frontend lint,
  types, tests with coverage and build, the API contract, breaking API changes, and the suppression ratchet of
  the whole repository;
- each section below has the summary and, in a collapsed `<details>`, the evidence: least covered files,
  broken contracts with the violating import, smoke scenarios with their boot time, new contract failures,
  surviving mutants with their diffs, lint problems, failures;
- ✅ passed, ⚠️ warning (ESLint warnings or models/migrations drift reported without failing, as with
  `SMOKE_STRICT_SCHEMA=0`; in CI both fail the job), ❌ failed,
  ⏭️ not run (job cancelled or skipped, or nothing to mutate). A job that failed before producing its result
  shows as ❌ with the job result, so the report never breaks.

The report only informs: each job is still the gate for its own checks, with the same thresholds. It is also
written to the job summary, which is the only place it appears on PRs from forks (their token cannot
comment). On pushes to `main`, the `quality` job also publishes the coverage badge shown in the README.

How it works: each job runs its tools through `scripts/quality_report.py run <analysis> -- <command>`, which
streams the output, keeps the exit code and stores a JSON fragment in `quality-fragments/`; the job uploads it
as the `quality-fragment-<job>` artifact. The `quality-report` job (`needs` every analysis job, `if: always()`)
downloads them and runs `scripts/quality_report.py render`. To add an analysis:

1. add a value to `Analysis` and an `analyze_<tool>` function returning a `Finding` in
   `scripts/quality_report.py`, registered in `ANALYZERS`;
2. add a `Check` to a `Section` in `SECTIONS` (or a new `Section`), with the job that runs it;
3. in `ci.yml`, run the tool through the wrapper (`if: ${{ !cancelled() }}` when it is not the first step),
   upload `quality-fragments/` as `quality-fragment-<job>` and, for a new job, add it to the `needs` of
   `quality-report`;
4. add tests in `tests/unit/scripts/test_quality_report.py` with a sample of the tool's real output.
