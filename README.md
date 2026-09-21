[![CI backend](https://img.shields.io/github/actions/workflow/status/softwareone-platform/ffc-extension/backend-tests.yaml?branch=main&label=CI%20backend&logo=github&logoColor=white)](https://github.com/softwareone-platform/ffc-extension/actions/workflows/backend-tests.yaml) [![CI frontend](https://img.shields.io/github/actions/workflow/status/softwareone-platform/ffc-extension/frontend-tests.yaml?branch=main&label=CI%20frontend&logo=github&logoColor=white)](https://github.com/softwareone-platform/ffc-extension/actions/workflows/frontend-tests.yaml)
[![License](https://img.shields.io/badge/license-Apache%202.0-D22128?logo=apache&logoColor=white)](LICENSE)

[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/) [![Backend Coverage](https://img.shields.io/sonar/coverage/softwareone-mpt-github_ffc-extension_backend?server=https%3A%2F%2Fsonarcloud.io&logo=sonarqubecloud&logoColor=white)](https://sonarcloud.io/summary/new_code?id=softwareone-mpt-github_ffc-extension_backend) [![Backend Quality Gate](https://img.shields.io/sonar/quality_gate/softwareone-mpt-github_ffc-extension_backend?server=https%3A%2F%2Fsonarcloud.io&logo=sonarqubecloud&logoColor=white)](https://sonarcloud.io/summary/new_code?id=softwareone-mpt-github_ffc-extension_backend) [![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev/) [![Node](https://img.shields.io/badge/node-24-5FA04E?logo=nodedotjs&logoColor=white)](https://nodejs.org/) [![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/) [![Jest](https://img.shields.io/badge/Jest-30-C21325?logo=jest&logoColor=white)](https://jestjs.io/) [![Frontend Coverage](https://img.shields.io/sonar/coverage/softwareone-mpt-github_ffc-extension_frontend?server=https%3A%2F%2Fsonarcloud.io&logo=sonarqubecloud&logoColor=white)](https://sonarcloud.io/summary/new_code?id=softwareone-mpt-github_ffc-extension_frontend) [![Frontend Quality Gate](https://img.shields.io/sonar/quality_gate/softwareone-mpt-github_ffc-extension_frontend?server=https%3A%2F%2Fsonarcloud.io&logo=sonarqubecloud&logoColor=white)](https://sonarcloud.io/summary/new_code?id=softwareone-mpt-github_ffc-extension_frontend)

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
- [`docs/conventions/modals.md`](docs/conventions/modals.md) — in-app modal pattern (`Modal`, `useModalToggle`, form controllers).
- [`docs/architecture/mpt-host-integration.md`](docs/architecture/mpt-host-integration.md) — iframe-as-extension runtime.
- [`docs/architecture/standalone-mode.md`](docs/architecture/standalone-mode.md) — `useHasMPTHost` / `useIsRootPage`.
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
