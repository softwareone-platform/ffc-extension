# Copilot / AI agent instructions

Python backend (`app/`), React + TypeScript frontend (`frontend/`),
Playwright e2e (`e2e/`). Canonical docs live in [`../docs/`](../docs); start
with [`../AGENTS.md`](../AGENTS.md) for the index.

## Frontend (`frontend/`)

When creating or refactoring files under `frontend/src`, follow the naming
convention in
**[`../docs/conventions/naming.md`](../docs/conventions/naming.md)**.

TL;DR:

- **Folders** — `kebab-case` (`page-shell/`, `data-sources/`).
- **Components / providers / layouts** — `PascalCase.tsx` matching the export.
- **Hooks** — `camelCase.ts` starting with `use`.
- **Companion files** — share the PascalCase base with a `.` qualifier
  (`OrganizationsGrid.config.tsx`, `DetailsLayout.scss`).
- **Barrels** — `index.ts`, re-export from PascalCase files.
- **Path aliases** (`~app`, `~features`, `~shared`, `~organizations`,
  `~entitlements`, `~i18n`, `~styles`) — target `kebab-case` folders.

For data fetching, follow
[`../docs/conventions/api-hooks.md`](../docs/conventions/api-hooks.md):
list endpoints get `useFooApi.tsx` (raw HTTP callbacks), detail endpoints
get `useFooDetailsApi.ts` (`useQuery` wrapper with the
`["Entity", "Details", id]` key). Don't inline `useQuery` in components.

For UI strings use `useFixedT("prefix")` (not raw `useTranslation`) — see
[`../docs/conventions/i18n.md`](../docs/conventions/i18n.md). Key separator
is `:`. Top-level namespaces are `<feature>` and `shared`. Mirror API
field names in `snake_case`; use `camelCase` for UI-only labels.

For modals see [`../docs/conventions/modals.md`](../docs/conventions/modals.md).
Every "create" modal ships as a pair: `Create<Entity>EntryModal` (host-mounted)
+ `Create<Entity>StandaloneModal` (in-app), sharing a `use<Entity>FormController`.

### Runtime context

The frontend runs in two modes (embedded inside MPT host, or standalone).
Before adding behavior that varies between them, read
[`../docs/architecture/standalone-mode.md`](../docs/architecture/standalone-mode.md)
to pick the right hook (`useHasMPTHost` / `useIsRootPage` /
`useIsStandaloneShell` are **not** interchangeable). For how the host bridge
is detected, see
[`../docs/architecture/mpt-host-integration.md`](../docs/architecture/mpt-host-integration.md).

Each file in `frontend/src/entries/` is a separate esbuild bundle (standalone
SPA, per-feature, or per-modal). When adding an entry, see
[`../docs/architecture/entry-mode.md`](../docs/architecture/entry-mode.md).

### Renames

1. Use `git mv` to preserve history.
2. For case-only renames on macOS, do a two-step rename through a temp name.
3. Update every import: barrels (`index.ts`), aliased imports, dynamic
   `import('…')` calls (e.g. inside `lazyComponent(…)`), and `./*.scss`
   siblings.
4. Verify with `cd frontend && npx tsc --noEmit`. Restart the TS server in
   the editor if it still reports `TS1149` / `TS1261` after a clean `tsc`.

Do not rename: `index.ts`, `package.json`, `tsconfig*.json`,
`esbuild.config.js`, `eslint.config.mjs`, `global.d.ts`, locale JSON files,
or anything in `node_modules/`.

## Backend (`app/`)

Python project managed with `uv` + Alembic. See top-level
[`../README.md`](../README.md) for run instructions.
