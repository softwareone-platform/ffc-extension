# AGENTS.md

Guidance for AI coding agents working in this repository.

## Precedence (who wins on drift)

Three sources describe the same conventions at different depths. When they
contradict, follow this order:

1. **[`docs/conventions/*`](docs/conventions/)** — human-authored, team-wide,
   canonical. Always wins. See [`docs/README.md`](docs/README.md) for the
   full index.
2. **[`.claude/skills/*/SKILL.md`](.claude/skills/)** — Claude Code
   lazy-loaded skills. Layer code recipes and Claude-coaching metadata on
   top of the convention docs; defer to them for anything they cover.
3. **[`.github/copilot-instructions.md`](.github/copilot-instructions.md)**
   — Copilot inline mirror of the most load-bearing rules (Copilot can't
   lazy-load SKILL.md). Lowest priority; drift here first.

**When updating a rule**, start at the top of the chain and propagate down.
When reading, trust the top of the chain.

- **Frontend file & folder naming** (imports, renames, translation keys):
  [`docs/conventions/naming.md`](docs/conventions/naming.md).
- **API hook conventions** (`useFooApi` vs `useFooDetailsApi`, query keys):
  [`docs/conventions/api-hooks.md`](docs/conventions/api-hooks.md).
- **i18n conventions** (`useFixedT`, namespaces, dynamic keys, locales):
  [`docs/conventions/i18n.md`](docs/conventions/i18n.md).
- **Modal conventions** (in-app modals, `useModalToggle`, shared controllers):
  [`docs/conventions/modals.md`](docs/conventions/modals.md).
- **Design system & presentation** (subpath imports, verified DS gaps, icon
  names, SCSS tokens, `.ffc-*` classes, chart palettes):
  [`docs/conventions/design-system.md`](docs/conventions/design-system.md).
- **Design system component usage** (Panel + KpiTile, Grid with sort/filter,
  Modal vs app wrapper, Charts, Multi-select composition, Navigation shell,
  Chip, DatePicker):
  [`docs/conventions/design-system-components.md`](docs/conventions/design-system-components.md).
- **Frontend testing conventions** (jest/testing-library mocking rules,
  shared `~test-utils`, coverage floor, test-name style):
  [`docs/conventions/testing.md`](docs/conventions/testing.md).
- **MPT host integration** (iframe-as-extension runtime, `__MPT__` detection,
  `useHasMPTHost` vs `useIsRootPage`):
  [`docs/architecture/mpt-host.md`](docs/architecture/mpt-host.md).
- **General Copilot instructions** (mirrors what GitHub Copilot loads):
  [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
- **Claude Code skills** (lazy-loaded; `docs/conventions/*` wins on drift). The `mpt-*` skills are **portable across MPT frontend projects**; concrete project values live in a sibling project bindings skill:
  - Baseline frontend conventions (TS discipline, Fast Refresh, verify commands) — [`.claude/skills/mpt-frontend-standards/SKILL.md`](.claude/skills/mpt-frontend-standards/SKILL.md).
  - `@swo/design-system` component usage (Grid, Modal, Panel, Charts, Multi-select, Navigation) — [`.claude/skills/mpt-design-system/SKILL.md`](.claude/skills/mpt-design-system/SKILL.md).
  - Sandbox / POC frontend work (folder layout, mock data layer, scaling patterns) — [`.claude/skills/mpt-poc-builder/SKILL.md`](.claude/skills/mpt-poc-builder/SKILL.md).
  - Jest unit tests under `frontend/src/**/*.spec.{ts,tsx}` — [`.claude/skills/mpt-module-testing/SKILL.md`](.claude/skills/mpt-module-testing/SKILL.md).
  - **Project-specific bindings** (alias names, CSS prefix, wrapper paths, entity list, test-utils inventory) — [`.claude/skills/ffc-extension/SKILL.md`](.claude/skills/ffc-extension/SKILL.md). In another MPT project replaced by that project's project bindings skill.

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

