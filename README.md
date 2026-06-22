[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_ffc-extension&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_ffc-extension) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_ffc-extension&metric=coverage)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_ffc-extension)

# SoftwareOne FinOps for Cloud Extension

The FinOps for Cloud Extension enables SoftwareOne to manage the FinOps for Cloud tool. It supports the provisioning and administration of FinOps for Cloud organizations and users, as well as the management of datasource entitlements.

## Repo layout

- `backend/` — Python backend (FastAPI + SQLAlchemy + Alembic); Alembic migrations under `backend/migrations/`.
- `frontend/` — React + TypeScript extension UI, bundled with esbuild.
- `static/` — esbuild output (do not edit by hand).
- `e2e/` — Playwright end-to-end tests.
- `docs/` — conventions and architecture notes (see below).

## Documentation

- [`AGENTS.md`](AGENTS.md) — guidance for AI coding agents (and humans) working in this repo.
- [`docs/conventions/naming.md`](docs/conventions/naming.md) — frontend file & folder naming.
- [`docs/conventions/api-hooks.md`](docs/conventions/api-hooks.md) — `useFooApi` vs `useFooDetailsApi` patterns.
- [`docs/conventions/i18n.md`](docs/conventions/i18n.md) — translation namespaces, `useFixedT`, dynamic keys.
- [`docs/conventions/modals.md`](docs/conventions/modals.md) — entry vs standalone modal pair pattern.
- [`docs/architecture/entry-mode.md`](docs/architecture/entry-mode.md) — `mountStandaloneEntry` / `mountFeatureEntry` / `mountModalEntry`.
- [`docs/architecture/mpt-host-integration.md`](docs/architecture/mpt-host-integration.md) — iframe-as-extension runtime.
- [`docs/architecture/standalone-mode.md`](docs/architecture/standalone-mode.md) — `useHasMPTHost` / `useStandAloneApp` / `useIsStandaloneShell`.
- [`docs/dev/devcontainer.md`](docs/dev/devcontainer.md) — devcontainer setup.

# Create your .env file

You can use the `env.example` as a base to set up your running environment and customize it according to your needs.

# Run tests

`docker compose run --rm app_test`

# Run for Development

`docker compose up app`

This runs `ffcops serve -w2 --ziti-load-timeout-ms 20000` inside the `app`
container (see `docker-compose.yaml`). To override worker count or any other
`serve` flag, run the CLI directly:

```sh
docker compose run --rm --service-ports app uv run ffcops serve --server-workers 4
```

See `uv run ffcops serve --help` for the full flag list (`--server-backlog`,
`--server-timeout-keep-alive`, `--server-reload`, etc.).

# Build production image

To build the production image please use the `prod.Dockerfile` dockerfile.

> [!IMPORTANT]
> Developers must take care of keep in sync `dev.Dockerfile` and `prod.Dockerfile`.
