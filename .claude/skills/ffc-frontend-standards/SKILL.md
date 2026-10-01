---
name: ffc-frontend-standards
description: Cross-cutting frontend conventions for ffc-extension — path aliases, design-system subpath imports, TypeScript discipline (no `any`, derived prop/return types), file-extension and Fast-Refresh rules, icon and SCSS token hygiene, i18n via useFixedT, verification commands (tsc, build, prettier, eslint), and the "don't invent, reuse" ethos. Baseline shared by `ffc-poc-builder` and `mpt-module-testing`. Use when touching any frontend code (component, hook, utility, shared module, type, SCSS, i18n key) that isn't clearly a new POC or a new test.
---

# ffc-extension Frontend Standards

Baseline conventions used by every file under `frontend/src/`. The feature-specific skills (`ffc-poc-builder`, `mpt-module-testing`) assume everything here already holds.

## Path aliases

Configured in `frontend/tsconfig.json` + `jest.config.js`. Always import by alias — never climb `../../../`.

| Alias           | Points at                       | Use for                                                                     |
| --------------- | ------------------------------- | --------------------------------------------------------------------------- |
| `~shared/*`     | `frontend/src/shared/*`         | Hooks, utils, UI primitives, styles, mock helpers reused across features    |
| `~features/*`   | `frontend/src/features/*`       | Cross-feature references (e.g. `~features/organizations/paths`)             |
| `~api/*`        | `frontend/src/api/*`            | Generated/shared API types (`ffc-api-model`)                                |
| `~test-utils/*` | `frontend/src/test-utils/*`     | Render wrappers, factories, shared jest mocks — spec files only             |

Rule of thumb: if the file lives outside the current feature folder, use the alias.

## Design-system imports

**Always subpath**: `@swo/design-system/button`, `@swo/design-system/grid`, `@swo/design-system/chip`, `@swo/design-system/navigation`, etc. **Never root** `@swo/design-system`.

Why — two reasons that compound:

1. **Bundle size**: subpath imports cost 100s of KB each; the root barrel pulls everything (see `project-frontend-bundle-facts` memory).
2. **Mock resolution**: `jest.mock("@swo/design-system/grid", …)` only matches the exact path the source imports. A root-barrel source + subpath mock (or vice-versa) silently no-ops.

**Design tokens**: `@swo/design-tokens` — SCSS only. In amCharts configs use raw hex via `CHART_COLORS` (CSS vars haven't resolved yet when amCharts reads them).

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

- `.ts` — pure logic, types, hooks, utilities, factories, mock-module shapes.
- `.tsx` — files that return JSX.
- `.spec.ts` / `.spec.tsx` — unit tests (never `.test.*`).
- `.spec.mocks.ts[x]` — sibling file holding `jest.mock(...)` prelude for a spec. **Must sort before the source-under-test import** — `frontend/.prettierrc.json` has a dedicated import group for this; don't reorder.

**`react-refresh/only-export-components`** forbids mixing component + non-component exports in the same `.tsx`. Any Provider that owns a context + hook must be split:

- `FooContext.ts` — `createContext`, hook (`useFoo`), value type
- `FooProvider.tsx` — only exports the Provider component

Downstream imports stay stable (`import { useFoo } from "./FooContext"` resolves to the new `.ts` automatically).

## Icon + SCSS token hygiene — do not guess

**Icons** (`@swo/design-system/icon`): strict string-literal union. `arrow_drop_down`, `arrow_down`, etc. don't exist. Common ones: `expand_more` (dropdowns), `arrow_forward_ios` / `arrow_back_ios` (chevrons), `info`, `filter_alt`. Before using an unfamiliar name:

```text
ls frontend/node_modules/@swo/design-system/icon/src/lib/icon-paths/
```

**SCSS tokens** (`frontend/src/shared/styles/_tokens.scss`): fixed vocabulary. Invented names like `$primary`, `$danger`, `$warning` do not exist and the build fails silently from `npm run typecheck` — only `npm run build` catches it.

| Alias                           | Use for                                              |
| ------------------------------- | ---------------------------------------------------- |
| `$surface`, `$surface-muted`    | Backgrounds (white, muted gray)                      |
| `$border-subtle`                | 1 px borders                                         |
| `$text-muted`, `$text-strong`   | Secondary / primary text colour                      |
| `$positive`, `$negative`        | Up / down / success / danger text colour             |
| `$space-xs` … `$space-xl`       | `--spacing-0.5` through `--spacing-4`                |
| `$radius-card`                  | Card / panel rounding (8 px)                         |
| `$panel-grid-breakpoint`        | Breakpoint where 2-col grid collapses to 1          |

## i18n

- **Namespace**: `"<feature>": { … }` in `src/i18n/en.json`.
- **Access**: `const t = useFixedT("<feature>:<section>")` then `t("key")`. One hook per section used, not one for the whole feature.
- **Alphabetised keys** within each object — the `translations:sort` script enforces this; sort before committing.
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

If a Storybook/shared primitive **partially** matches: stop and ask. Don't silently invent a look-alike. (POC-side rationale in `ffc-poc-builder`; test-side in `mpt-module-testing`.)

## Extraction threshold

Promote something into shared infrastructure (`~shared`, `~test-utils/mocks`, a feature-local primitive) **when the second duplicate appears** — not before. Day-one abstraction before the shape has stabilised freezes guesses as structure.

Rule of thumb per surface:

- **Jest module mock**: 2+ specs with equivalent factory → `~test-utils/mocks/<name>.ts`.
- **Composable UI primitive** (e.g. `MetricPanel`): 3+ identical compositions → feature-local `components/<Name>.tsx`.
- **React-query hook body**: 3+ hooks differing only by key + fetcher → single factory (`createMetricsQuery`).
- **Chart config / palette**: 2+ tabs declare module-scope series → feature-local `chartConfig.ts`.

## Universal anti-patterns

- Root `@swo/design-system` imports — bundle-size regression + mock resolution breaks.
- `any` or untyped `jest.fn()` — type-drift surfaces at runtime, far from the cause.
- Inline response / prop shapes when `ComponentProps<typeof C>` / a model-file type exists.
- Guessing SCSS token or icon names — grep first.
- Hardcoded strings in JSX / in Chart config — break i18n.
- Mixing a component with a hook/type/context export in the same `.tsx` — breaks Fast Refresh.
- Importing JSON directly in a tab/component — breaks the swap-to-real-API story (POC) and makes mocks ambiguous (tests).
- Rebuilding referentially-sensitive arrays (chart series, memo deps, `useQuery` options) inside the component body — triggers rebuilds / refetches on every render.
- Climbing `../../../` instead of using a path alias.
- Promoting shared primitives on day one — add them when the second duplicate appears.

## Pointers to feature-specific skills

- Building a new sandbox view, tab, grid, chart, side-nav, filter sidebar, or any mock-driven UI → **`ffc-poc-builder`** (folder layout, DS gap table, panel/chart/grid recipes, scaling patterns).
- Writing or refactoring a `*.spec.tsx` — Grid wrapper, Details container, hook, action, wizard, modal callback, API hook → **`mpt-module-testing`** (jest mock rules, shared `~test-utils/mocks/`, spec file layout, canonical patterns).
