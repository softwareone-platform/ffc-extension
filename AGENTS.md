# AGENTS.md

Guidance for AI coding agents working in this repository.

- **Frontend conventions** (file & folder naming, imports, renames):
  see [`frontend/NAMING.md`](frontend/NAMING.md).
- **General Copilot instructions** (mirrors what GitHub Copilot loads):
  see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Repo layout

- `app/` — Python backend (FastAPI + SQLAlchemy + Alembic).
- `frontend/` — React + TypeScript extension UI, bundled with esbuild.
- `e2e/` — Playwright end-to-end tests.
- `migrations/` — Alembic migrations.
- `static/` — esbuild output (do not edit by hand).

## Before changing code

1. Match the existing style and naming of the surrounding folder.
2. For frontend changes, read `frontend/docs/conventions/naming.md` first.
3. After edits, run the relevant verification:
   - Frontend: `cd frontend && npx tsc --noEmit`
   - Backend: existing test suite under `tests/`.

## Do not touch

- Generated output in `static/`.
- Anything under `node_modules/`.
- `pg_data/` (Postgres data directory).
