# AGENTS.md

Guidance for AI coding agents working in this repository.

- **Frontend file & folder naming** (imports, renames, translation keys):
  [`docs/conventions/naming.md`](docs/conventions/naming.md).
- **API hook conventions** (`useFooApi` vs `useFooDetailsApi`, query keys):
  [`docs/conventions/api-hooks.md`](docs/conventions/api-hooks.md).
- **i18n conventions** (`useFixedT`, namespaces, dynamic keys, locales):
  [`docs/conventions/i18n.md`](docs/conventions/i18n.md).
- **Modal conventions** (entry vs standalone shapes, shared controllers):
  [`docs/conventions/modals.md`](docs/conventions/modals.md).
- **Entry modes** (esbuild bundles per `src/entries/*`, `mount*Entry` helpers):
  [`docs/architecture/entry-mode.md`](docs/architecture/entry-mode.md).
- **MPT host integration** (iframe-as-extension runtime, `__MPT__` detection):
  [`docs/architecture/mpt-host-integration.md`](docs/architecture/mpt-host-integration.md).
- **Standalone mode flags** (`useHasMPTHost` vs `useIsRoot` vs
  `useIsStandaloneShell`): [`docs/architecture/standalone-mode.md`](docs/architecture/standalone-mode.md).
- **General Copilot instructions** (mirrors what GitHub Copilot loads):
  [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Repo layout

- `backend/` — Python backend (FastAPI + SQLAlchemy + Alembic). Code in `backend/app/`, Alembic migrations in `backend/migrations/`, tests in `backend/tests/`.
- `frontend/` — React + TypeScript extension UI, bundled with esbuild.
- `e2e/` — Playwright end-to-end tests.
- `static/` — esbuild output (do not edit by hand).

## Before changing code

1. Match the existing style and naming of the surrounding folder.
2. For frontend changes, read `docs/conventions/naming.md` first.
3. After edits, run the relevant verification:
   - Frontend: `cd frontend && npx tsc --noEmit`
   - Backend: `cd backend && uv run pytest`.

## Do not touch

- Generated output in `static/`.
- Anything under `node_modules/`.
- `pg_data/` (Postgres data directory).

