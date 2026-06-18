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

## MPT host integration (iframe-as-extension)

The frontend can run two ways: embedded inside the MPT host shell, or
standalone. The host injects `globalThis.__MPT__` into the iframe around mount
time. Key pieces:

- `frontend/src/global.d.ts` — types `globalThis.__MPT__` (single source of
  truth; do not redeclare elsewhere).
- `frontend/src/shared/providers/MPTContextProvider.tsx` — polls for
  `__MPT__` via `useSyncExternalStore`, with a 5s safety timeout so standalone
  mode doesn't poll forever. Exposes `useHasMPTHost()` (also re-used by other
  hooks) and `MPTContextProvider` which switches between an empty provider
  (standalone) and `HostContextBridge` (embedded).
- `frontend/src/shared/hooks/useNotifyParentChildModal.ts` — when this app
  opens a child modal inside the iframe, it emits a `child-modal` event so the
  host can dim its own header. A single effect handles open/close *and* the
  unmount-while-open case via React's effect cleanup.

**Replacing the polling.** The 5s-bounded polling is a workaround because the
host doesn't currently signal injection completion. If the host team adds a
`mpt:ready` window event (or guarantees `__MPT__` is set before our bundle
loads), `subscribeToHost` can be replaced with a one-shot `addEventListener`.
