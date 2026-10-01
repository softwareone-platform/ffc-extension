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
  (`OrganizationsGrid.config.tsx`, `StandaloneRoot.scss`).
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
Modals are in-app: a `Create<Entity>Modal` wrapping `<Modal>`,
its open/close state driven by `useModalToggle`, with form logic in a shared
`use<Entity>FormController`.

For design-system usage — subpath imports (`@swo/design-system/<component>`,
never root), verified gaps (multi-select, DonutChart default height, strict
`Icon.name` union), SCSS token vocabulary (`$surface`, `$positive`, `$space-*`),
and the shared `.ffc-*` layout classes — see
[`../docs/conventions/design-system.md`](../docs/conventions/design-system.md).

### Claude Code skills (not loaded by Copilot)

Claude Code can lazy-load these; Copilot cannot. If a frontend task falls into
one of these buckets, the canonical rules live in the SKILL.md — this file does
NOT mirror them inline (keeping sync tax to the one testing section below).
`docs/conventions/*` still wins on drift against any skill.

- Baseline frontend conventions (path aliases, DS subpath imports, derived TS
  types, Fast Refresh file-split, icon/SCSS token hygiene, verify commands,
  extraction thresholds) —
  [`../.claude/skills/mpt-frontend-standards/SKILL.md`](../.claude/skills/mpt-frontend-standards/SKILL.md).
- Sandbox / POC work (feature folder layout, DS component gap table,
  panel/chart/grid recipes, mock-driven data layer, `<MetricPanel>` and chart
  config patterns) —
  [`../.claude/skills/mpt-poc-builder/SKILL.md`](../.claude/skills/mpt-poc-builder/SKILL.md).

### Frontend unit tests

For frontend unit tests under `frontend/src/**/*.spec.{ts,tsx}` and sibling
`.spec.mocks.ts[x]` helpers, the canonical doc is
[`../docs/conventions/testing.md`](../docs/conventions/testing.md); the Claude
skill [`../.claude/skills/mpt-module-testing/SKILL.md`](../.claude/skills/mpt-module-testing/SKILL.md)
layers recipes on top. The rules below are mirrored inline **for Copilot**
(which can't lazy-load either). **When updating a rule, edit all three** —
`docs/conventions/testing.md` wins on drift, then SKILL.md, then this file.

Key rules Copilot should apply directly:

- Coverage must stay **above 85%**.
- Use real source types in specs and mocks: prefer
  `ComponentProps<typeof X>`, `Pick<ComponentProps<typeof X>, ...>`, exported
  app prop types, and `ReturnType<typeof useHook>` over handwritten `type
FooProps = { ... }` copies.
- Prefer existing shared test utilities and mocks from `~test-utils`,
  especially `renderWithRouter`, `renderWithEntitlementRoute`,
  `renderWithOrganizationRoute`, `renderCell`, modal trigger helpers,
  `mockFixedT`, and `mockDesignSystemButton`.
- Mock the exact design-system import path (`@swo/design-system/...`) and do
  not spread `jest.requireActual()` from large design-system modules.
- Avoid low-value tests: path literal assertions, exhaustive router smoke
  coverage that only restates route wiring, and inline snapshots for simple DOM
  structure or attributes.
- Keep test names behaviour-focused: avoid `noop`, raw assertion fragments like
  `-> isHidden=%s` / `-> isDisabled=%s`, and URL-heavy route names when a tab
  or scenario label is clearer.
- For API-hook specs, prefer behaviour-focused titles like `fetches X by id`
  or `lists X using the provided query` over raw HTTP verb/path descriptions.
- Prefer explicit behavioural assertions over snapshots; assert text, roles,
  classes, callback wiring, and meaningful props.

### Runtime context

The app ships as a single standalone bundle that can run inside the MPT host
iframe or loaded directly. Before adding behavior that varies with host
presence, read
[`../docs/architecture/mpt-host.md`](../docs/architecture/mpt-host.md) — it
covers how the host bridge is detected and which of the two host-presence
hooks to pick (`useHasMPTHost` and `useIsRootPage` are **not**
interchangeable).

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
