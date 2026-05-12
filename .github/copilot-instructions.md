# Copilot / AI agent instructions

This repository contains a Python backend (`app/`), a React + TypeScript
frontend (`frontend/`), and Playwright e2e tests (`e2e/`).

## Frontend (`frontend/`)

When creating or refactoring files under `frontend/src`, follow the file &
folder naming convention documented in **[`frontend/docs/conventions/naming.md`](../frontend/docs/conventions/naming.md)**.

Quick reference:

- **Folders**: `kebab-case` (`page-shell/`, `data-sources/`).
- **Components / providers / layouts**: `PascalCase.tsx` matching the export
  (`PageShell.tsx`, `OrganizationsGrid.tsx`, `ExtensionsProvider.tsx`).
- **Hooks**: `camelCase` starting with `use` (`useFixedT.ts`,
  `useReactQueryRqlGrid.ts`).
- **Companion files** share the PascalCase base with a `.` qualifier
  (`OrganizationsGrid.config.tsx`, `DetailsLayout.scss`,
  `useReactQueryRqlGrid.spec.tsx`).
- **Barrel** files stay `index.ts` and re-export from PascalCase files.
- TS path aliases (`~app`, `~features`, `~organizations`, `~shared`,
  `~i18n`, `~styles`) target `kebab-case` folders; only file suffixes are
  PascalCase / camelCase.

When renaming:

1. Use `git mv` to preserve history.
2. For case-only renames on macOS, do a two-step rename through a temp name.
3. Update every import: barrels (`index.ts`), aliased imports,
   dynamic `import('…')` in `frontend/src/app/router.tsx`, and `./*.scss`
   siblings.
4. Verify with `cd frontend && npx tsc --noEmit`. Restart the TS server in
   the editor if it still reports `TS1149` / `TS1261` after a clean `tsc`.

Do not rename: `index.ts`, `package.json`, `tsconfig*.json`,
`esbuild.config.js`, `eslint.config.mjs`, `global.d.ts`, locale JSON files,
or anything in `node_modules/`.

## Backend (`app/`)

Python project managed with `uv` + Alembic. See top-level `README.md` for run
instructions.
