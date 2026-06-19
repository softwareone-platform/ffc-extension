[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_ffc-extension&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_ffc-extension) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_ffc-extension&metric=coverage)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_ffc-extension)

# SoftwareOne FinOps for Cloud Extension

The FinOps for Cloud Extension enables SoftwareOne to manage the FinOps for Cloud tool. It supports the provisioning and administration of FinOps for Cloud organizations and users, as well as the management of datasource entitlements.

## Repo layout

- `app/` — Python backend (FastAPI + SQLAlchemy + Alembic).
- `frontend/` — React + TypeScript extension UI, bundled with esbuild.
- `e2e/` — Playwright end-to-end tests.
- `migrations/` — Alembic migrations.
- `docs/` — conventions and architecture notes (see below).

## Documentation

- [`AGENTS.md`](AGENTS.md) — guidance for AI coding agents (and humans) working in this repo.
- [`docs/conventions/naming.md`](docs/conventions/naming.md) — frontend file & folder naming.
- [`docs/conventions/api-hooks.md`](docs/conventions/api-hooks.md) — `useFooApi` vs `useFooDetailsApi` patterns.
- [`docs/architecture/entry-mode.md`](docs/architecture/entry-mode.md) — `mountStandaloneEntry` / `mountFeatureEntry` / `mountModalEntry`.
- [`docs/architecture/mpt-host-integration.md`](docs/architecture/mpt-host-integration.md) — iframe-as-extension runtime.
- [`docs/architecture/standalone-mode.md`](docs/architecture/standalone-mode.md) — `useHasMPTHost` / `useStandAloneApp` / `useIsStandaloneShell`.
- [`docs/dev/devcontainer.md`](docs/dev/devcontainer.md) — devcontainer setup.

# Create you .env file

You can use the `env.example` as a bases to setup your running environment and customize it according to your needs.

# Run tests

`docker compose run --rm app_test`

# Run for Development

`docker compose up app`

# Build production image

To build the production image please use the `prod.Dockefile` dockerfile.

> [!IMPORTANT]
> Developers must take care of keep in sync `dev.Dockerfile` and `prod.Dockerfile`.
