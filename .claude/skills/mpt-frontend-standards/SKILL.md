---
name: mpt-frontend-standards
description: Cross-cutting frontend conventions for ffc-extension — path aliases, design-system subpath imports, TypeScript discipline (no `any`, derived prop/return types), file-extension and Fast-Refresh rules, icon and SCSS token hygiene, i18n via useFixedT, verification commands (tsc, build, prettier, eslint), and the "don't invent, reuse" ethos. Baseline shared by `mpt-poc-builder` and `mpt-module-testing`. Use when touching any frontend code (component, hook, utility, shared module, type, SCSS, i18n key) that isn't clearly a new POC or a new test.
---

# ffc-extension Frontend Standards

Baseline conventions used by every file under `frontend/src/`. The feature-specific skills (`mpt-poc-builder`, `mpt-module-testing`) assume everything here already holds.

**Canonical source of truth** — the project maintains these docs; this skill defers to them on every topic they cover:

| Topic                                           | Canonical doc                                              |
| ----------------------------------------------- | ---------------------------------------------------------- |
| File & folder naming                            | [`docs/conventions/naming.md`](../../../docs/conventions/naming.md)       |
| API hook shapes + query keys                    | [`docs/conventions/api-hooks.md`](../../../docs/conventions/api-hooks.md) |
| i18n (namespaces, dynamic keys)                 | [`docs/conventions/i18n.md`](../../../docs/conventions/i18n.md)           |
| Modals + form controllers                       | [`docs/conventions/modals.md`](../../../docs/conventions/modals.md)       |
| Design system (imports, gaps, icons, tokens)    | [`docs/conventions/design-system.md`](../../../docs/conventions/design-system.md) |
| Design system component usage (Panel, Grid, Modal, Charts, Multi-select, Navigation) | [`docs/conventions/design-system-components.md`](../../../docs/conventions/design-system-components.md) |
| Frontend unit tests                             | [`docs/conventions/testing.md`](../../../docs/conventions/testing.md)     |
| MPT host integration                            | [`docs/architecture/mpt-host.md`](../../../docs/architecture/mpt-host.md) |

This skill covers what those docs don't: path-alias reference, TypeScript derivation discipline, file-extension / Fast-Refresh split, verification commands, the "don't invent, reuse" ethos, and extraction thresholds.

## Path aliases

Configured in `frontend/tsconfig.json` + `jest.config.js`. Always import by alias — never climb `../../../`.

| Alias           | Points at                       | Use for                                                                     |
| --------------- | ------------------------------- | --------------------------------------------------------------------------- |
| `~shared/*`     | `frontend/src/shared/*`         | Hooks, utils, UI primitives, styles, mock helpers reused across features    |
| `~features/*`   | `frontend/src/features/*`       | Cross-feature references (e.g. `~features/organizations/paths`)             |
| `~api/*`        | `frontend/src/api/*`            | Generated/shared API types (`ffc-api-model`)                                |
| `~test-utils/*` | `frontend/src/test-utils/*`     | Render wrappers, factories, shared jest mocks — spec files only             |

Rule of thumb: if the file lives outside the current feature folder, use the alias.

## TypeScript discipline

- **No `any`.** Narrow via `unknown` or use a precise type. If a cast is unavoidable, cast as tight as possible at the call site (`as OrganizationRead`) — never cast the whole spy or hook.
- **Derive, don't duplicate.** Prefer source-exported types over handwritten prop shapes:
  - `ComponentProps<typeof C>` when the component doesn't export props
  - `Pick<ComponentProps<typeof C>, "a" | "b">` for the subset the consumer touches
  - `ReturnType<typeof useHook>` for a hook's return shape
  - `Parameters<typeof fn>` for a wrapper's args
- **Named types in dedicated files.** API shapes in `api/model.ts`; domain enums (const tuples + derived unions) alongside. React code imports pure types; API code imports constants + types. Dependency arrow points one way (React → model).
- **Enums or string-literal unions** for finite categorical values (`status: "trial" | "paid"`), never bare `string`.
- **Barrels re-export both runtime + types** (`export type { Foo }`, `export { useFoo }`). Only barrel the `api/` folder — don't add `components/index.ts` or `tabs/index.ts`; live features don't and the inconsistency isn't worth 4 chars.

## File extensions + Fast Refresh

File **casing** (PascalCase components, camelCase `use`-prefixed hooks, kebab-case folders, companion `.config.tsx` siblings, SCSS paired to component name) lives in [`docs/conventions/naming.md`](../../../docs/conventions/naming.md) — follow it.

Extension rules this skill adds on top:

- `.ts` — pure logic, types, hooks, utilities, factories, mock-module shapes.
- `.tsx` — files that return JSX.
- `.spec.ts` / `.spec.tsx` — unit tests (never `.test.*`).
- `.spec.mocks.ts[x]` — sibling file holding `jest.mock(...)` prelude for a spec. **Must sort before the source-under-test import** — `frontend/.prettierrc.json` has a dedicated import group for this; don't reorder.

**`react-refresh/only-export-components`** forbids mixing component + non-component exports in the same `.tsx`. Any Provider that owns a context + hook must be split:

- `FooContext.ts` — `createContext`, hook (`useFoo`), value type
- `FooProvider.tsx` — only exports the Provider component

Downstream imports stay stable (`import { useFoo } from "./FooContext"` resolves to the new `.ts` automatically).

## i18n

Full rules — namespaces (`<feature>` / `shared`), key separator (`:`), leaf casing (snake_case for API-mirror fields vs camelCase for UI-only labels), dynamic-key enumeration, adding a locale — in [`docs/conventions/i18n.md`](../../../docs/conventions/i18n.md). Highlights:

- `const t = useFixedT("<feature>:<section>")` then `t("key")`. Never raw `useTranslation()`. One hook per section used, not one for the whole feature.
- Alphabetised keys within each object — the `translations:sort` script enforces this; sort before committing.
- In **tests**, `useFixedT` is globally identity-mocked in `jest.setup.js`; the key passes through as text. Don't assert specific translation values — that only tests the mock.

## Verification before done

Run before considering any change finished:

```bash
cd frontend
npx tsc --noEmit                    # type-check
npm run build                       # catches SCSS token errors tsc misses
npx prettier --write <touched files>
npx eslint <touched files>
```

For test work, `npm test` runs jest + tsc + prettier + eslint in parallel via `npm-run-all --parallel --continue-on-error`. SWC skips type-checking during jest, so **typed-spy drift only surfaces at the tsc step** — don't trust a green jest run alone.

## After verification: offer unit tests

Once the verify step passes and before reporting the task done, **ask the user whether to check existing tests or add new ones** for the files you touched. If they accept, hand off to **`mpt-module-testing`** (which layers recipes on top of [`docs/conventions/testing.md`](../../../docs/conventions/testing.md)).

**When to ask:**

- Any task that changed source under `frontend/src/` — components, hooks, utilities, API shapes, context providers, feature modules.
- Any bug fix (regression tests close the loop).

**When to skip the ask:**

- The task **was** writing or fixing tests — no need to prompt about doing it again.
- Pure documentation changes (`docs/`, `README.md`, `SKILL.md`, `AGENTS.md`, this file).
- Pure configuration (`package.json`, `tsconfig.json`, `.prettierrc.json`, `eslint.config.mjs`, CI yaml).
- Rename-only / move-only changes that preserve existing test coverage automatically.
- The user already declined for this specific change.

**Phrasing** — one short line, concrete about the surface:

> "Want me to check or add unit tests for the files I touched (`<file1>`, `<file2>`, …)? I'd use the `mpt-module-testing` skill."

If accepted, identify the files worth testing (behaviour / branching, not pure types or barrels — see [`docs/conventions/testing.md`](../../../docs/conventions/testing.md) "When NOT to write a unit test"), then switch to `mpt-module-testing` for the actual spec work.

## "Don't invent, reuse"

Before building anything new, check whether it already exists:

| Need                              | Check first                                                                 |
| --------------------------------- | --------------------------------------------------------------------------- |
| UI widget / recipe                | https://storybook.platform.softwareone.com/ → use the DS package it ships from |
| Shared hook                       | `~shared/hooks/`                                                            |
| Mock factory for a jest module    | `~test-utils/mocks/`                                                        |
| Typed `Partial<T>`-overlay builder| `~test-utils/factories/`                                                    |
| Render wrapper (router, query)    | `~test-utils/` (`renderWithRouter`, `createQueryClientWrapper`, …)         |
| Date formatting                   | `useFormatDate` from `~shared/hooks/useFormatDate`                          |
| Shared layout class               | `~shared/styles/_components.scss` — look for `.ffc-*` modifiers             |
| Mock axios response               | `mockResponse` from `~shared/utils/mockResponse`                            |

If a Storybook/shared primitive **partially** matches: stop and ask. Don't silently invent a look-alike. (POC-side rationale in `mpt-poc-builder`; test-side in `mpt-module-testing`.)

## Extraction threshold

Promote something into shared infrastructure (`~shared`, `~test-utils/mocks`, a feature-local primitive) **when the second duplicate appears** — not before. Day-one abstraction before the shape has stabilised freezes guesses as structure.

Rule of thumb per surface:

- **Jest module mock**: 2+ specs with equivalent factory → `~test-utils/mocks/<name>.ts`.
- **Composable UI primitive** (e.g. `MetricPanel`): 3+ identical compositions → feature-local `components/<Name>.tsx`.
- **React-query hook body**: 3+ hooks differing only by key + fetcher → single factory (`createMetricsQuery`).
- **Chart config / palette**: 2+ tabs declare module-scope series → feature-local `chartConfig.ts`.

## Universal anti-patterns

- `any` or untyped `jest.fn()` — type-drift surfaces at runtime, far from the cause.
- Inline response / prop shapes when `ComponentProps<typeof C>` / a model-file type exists.
- Hardcoded strings in JSX / in chart config — break i18n.
- Mixing a component with a hook/type/context export in the same `.tsx` — breaks Fast Refresh.
- Importing JSON directly in a tab/component — breaks the swap-to-real-API story (POC) and makes mocks ambiguous (tests).
- Rebuilding referentially-sensitive arrays (chart series, memo deps, `useQuery` options) inside the component body — triggers rebuilds / refetches on every render.
- Climbing `../../../` instead of using a path alias.
- Promoting shared primitives on day one — add them when the second duplicate appears.

(DS-specific anti-patterns — root `@swo/*` imports, guessing icon names, inventing SCSS tokens — live in [`docs/conventions/design-system.md`](../../../docs/conventions/design-system.md).)

## Pointers to feature-specific skills

- Using `@swo/design-system/*` components (Grid, Modal, Panel, Charts, Chip, Popover, Icon, DatePicker, Navigation) or any `~shared/components/{panel, charts, modal}` wrapper → **`mpt-design-system`** (composition recipes, wrapper-vs-raw-DS decisions, gap-table workflow).
- Building a new sandbox view, tab, grid, chart, side-nav, filter sidebar, or any mock-driven UI → **`mpt-poc-builder`** (folder layout, mock data layer, scaling patterns, POC checklist).
- Writing or refactoring a `*.spec.tsx` — Grid wrapper, Details container, hook, action, wizard, modal callback, API hook → **`mpt-module-testing`** (jest mock rules, shared `~test-utils/mocks/`, spec file layout, canonical patterns).

## Pointers to workflow skills (git / PR / JIRA)

This skill only covers writing the code. For shipping it, hand off to the `mpt-ignite-skills` plugin:

- Starting a JIRA ticket → branch from master → **`start-feature`** (branch-name prefix by issue type, lowercase-dashes, pull-before-branch).
- Opening a PR against the right base branch → **`create-pr`** (merge-base-first vs. direct push, confirm description before submit).
- Writing a PR summary → **`summarize-pr`** (why-focused, short vs. structured by file count).
- Reviewing PR feedback → **`review-pr-comments`** (severity triage: Blocking / Suggestion / Question / Nit; grouped by topic, not speaker).
- Cherry-picking a landed commit onto a release branch → **`backport`** (branch from `origin/release/N`, oldest→newest, `-m 1` for merge parents, stop at conflicts).
