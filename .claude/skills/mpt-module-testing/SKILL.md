---
name: mpt-module-testing
description: Write unit tests for MPT modules (ffc-extension frontend). Jest + @testing-library/react + @swc/jest (CJS). Use for testing Grid components, Details containers, entity hooks, action components, wizard components, API hooks. Critical rules around design system import paths, pre-mocked modules, and gotchas around @mpt-extension/sdk.
---

# MPT Module Testing (ffc-extension)

Write unit tests for MPT modules following ffc-extension `frontend/` conventions.

Stack: `jest@30` + `@swc/jest` (CJS transform) + `jest-environment-jsdom` + `@testing-library/react@16`.

## Critical Rules

### File Extension
**ALWAYS** use `.spec.tsx` (NEVER `.test.tsx`).

### Design System Mocking — use the REAL import path
Source code imports from `@swo/design-system/[component]`. Mock **exactly** that path — `@swo/[component]` (the pattern from `mpt-vikings-ui`) does not match anything and the mock silently no-ops.

```typescript
// ✅ Correct — matches actual imports in this repo
jest.mock("@swo/design-system/grid", () => ({
  Grid: (props: unknown) => <div data-testid="grid" />,
  useGridAsync: jest.fn(),
  GridCellSimple: ({ children }) => <div>{children}</div>,
}));

// ❌ Wrong — no source file imports "@swo/grid"
jest.mock("@swo/grid", () => ({ ... }));
```

Return only the runtime exports the code under test actually uses at runtime; type-only exports are erased by SWC and don't need to be present.

### Globally enabled modules — DO NOT mock again

**Global node_modules mocks** live in `frontend/__mocks__/`.

Selected shared third-party mocks are enabled once in `frontend/jest.setup.js` via `jest.mock(...)` when the whole suite should see the same runtime module shape:

- `__mocks__/@swo/design-system/utils.tsx` — passes real exports through; overrides `useDesignSystemOptions`, `useLocalisation`, `DisplayValue`.

**Available root manual mocks (not assumed globally active):**

- `__mocks__/@mpt-extension/sdk.ts` — `{ setup, http }` stubs. Keep the file in root `__mocks__/` because the real package ships an ESM-only export.
- `__mocks__/react-router-dom.tsx` — pass-through mock that overrides `Link`; keep it for opt-in use, but do **not** enable it globally because route-param tests should keep the real router runtime by default.
- `__mocks__/react-i18next.tsx` — identity-style i18n mock for specs that import `react-i18next` directly.

**User-module mock** (aliased path — cannot use root `__mocks__/`, stays in `jest.setup.js`):

- `~shared/hooks/useFixedT` — returns identity function.

**Global setup** (also in `jest.setup.js`):

- `TextEncoder` / `TextDecoder` on `globalThis` — jsdom does not provide them; `react-router-dom` reaches for them at import time.
- explicit `jest.mock(...)` activation for the root manual mocks that are intentionally global
- `global.jest = jest` bridge — makes `jest.mock(...)` available in the ESM setup file.

### Never Mock
- `react` or `react-dom`
- The full `react-router-dom` module in a spec-specific factory (use `MemoryRouter` + `Routes` + `Route` for route params — don't stub `useParams`)

## Test File Placement

Co-locate tests with source files:
```
data-sources/
├── DataSources.tsx
├── DataSources.spec.tsx
├── DataSourcesGrid.tsx
├── DataSourcesGrid.spec.tsx
├── DataSourcesGrid.config.tsx
└── DataSourcesGrid.config.spec.tsx
```

## Test Wrappers

**Router (preferred for `useParams` — don't mock it):**
```typescript
<MemoryRouter initialEntries={["/organizations/org-123"]}>
  <Routes>
    <Route path="/organizations/:organizationId" element={<Component />} />
  </Routes>
</MemoryRouter>
```

**React Query:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});
<QueryClientProvider client={queryClient}>...</QueryClientProvider>
```

## Sharing Mocks Across Specs

`frontend/src/test-utils/` is the shared test-infrastructure root:

```
src/test-utils/
├── index.ts                     # barrel: createQueryClientWrapper, renderWithRouter, factories
├── renderWithQueryClient.tsx    # createQueryClientWrapper() — QueryClientProvider with retry: false
├── renderWithRouter.tsx         # renderWithRouter(ui, { initialUrl, routePath })
├── factories/                   # typed Partial<T>-overlay builders (e.g. makeDatasource)
└── mocks/                       # shared mock factories (see Option A below)
```

Two mock-sharing options, matched to the situation:

### Option A — Shared factory library (opt-in per spec) — the ffc-extension default

For mocks reused across a few specs where each spec exercises a different subset of the mocked module's surface, keep them in `src/test-utils/mocks/` and import them.

Constraints that shape the pattern:
- Jest hoists `jest.mock(...)` above imports; the factory can only reference imported bindings or variables whose name starts with `mock` (case-insensitive). **Both should hold** — prefix module-shape exports with `mock*` AND import them statically.
- ESLint's `@typescript-eslint/no-require-imports` blocks `require(...)` inside the factory. Static imports only.

```tsx
// src/test-utils/mocks/designSystemGrid.tsx
import { ReactNode } from "react";

export const mockGridProps = jest.fn();
export const mockUseGridAsync = jest.fn();

export const mockDesignSystemGrid = {
  Grid: (props: unknown) => {
    mockGridProps(props);
    return <div data-testid="grid" />;
  },
  GridCellSimple: ({ children }: { children: ReactNode }) => (
    <div data-testid="grid-cell-simple">{children}</div>
  ),
  useGridAsync: (config: unknown) => mockUseGridAsync(config),
};
```

```tsx
// Feature.spec.tsx
import { mockDesignSystemGrid, mockGridProps } from "~test-utils/mocks/designSystemGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
```

The imported spies (`mockGridProps`, `mockUseGridAsync`) are the same instances the mock factory references, so `mockReturnValue` / `.mock.calls` in the test drive what the code-under-test sees. `clearMocks: true` in `jest.config.js` resets them between tests automatically.

Existing shared mocks:
- `~test-utils/mocks/designSystemGrid` — `Grid`, `GridCellSimple`, `useGridAsync`, `buildRqlQuery`
- `~test-utils/mocks/entityReferenceCell` — `EntityReferenceCell`
- `~test-utils/mocks/sharedGridCells` — `CustomIcon`, `GridCellCurrency`, `GridCellDate`, `GridCellDynamicActions`

### Option B — Per-spec sibling helper (`<file>.spec.mocks.ts[x]`)

For a spec whose prelude of local `jest.mock` + `mock*` spies exceeds ~20-30 lines, touches more than 2-3 mocked modules, or simply reads like a “mock wall”, extract the entire prelude into a **sibling file next to the spec**: `<Feature>.spec.mocks.ts` (or `.tsx` if a factory returns JSX). The spec then imports only the spies and stays focused on setup helpers + `describe`.

```tsx
// DataSourcesGrid.config.spec.mocks.ts
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";

// Re-export shared spies the spec asserts against
export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

// Local spies live here — must still start with `mock*`
export const mockUseOrganizationContext = jest.fn();
export const mockUseUserRole = jest.fn();

// jest.mock calls — hoisted per-file, but Jest applies them to the test's
// module registry when the sibling is imported from the spec.
jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~organizations/providers/OrganizationsProvider", () => ({
  useOrganizationContext: () => mockUseOrganizationContext(),
}));
jest.mock("~shared/hooks/useUserRole", () => ({
  useUserRole: () => mockUseUserRole(),
}));
```

```tsx
// DataSourcesGrid.config.spec.tsx
import { renderHook } from "@testing-library/react";

import {
  mockUseGridAsync,
  mockUseOrganizationContext,
  mockUseUserRole,
} from "./DataSourcesGrid.config.spec.mocks";

import { useColumns } from "./DataSourcesGrid.config";

describe("DataSourcesGrid.config", () => { ... });
```

Constraints that shape the pattern:
- Same directory as the spec — relative paths (`./hooks/useActionOptions`) inside `jest.mock` calls resolve identically from either file.
- Spies still start with `mock*` (Jest's guardrail applies regardless of file).
- `jest.mock` calls in the sibling file *do* apply to the spec's test run — verified: Jest registers mocks in the per-test module registry as soon as the file is imported.
- **When NOT to extract:** if the prelude is small (<20 lines) or if hiding the mock setup would confuse a future reader more than it saves lines. Small preludes stay inline — one file to open, one to reason about.

Canonical examples: `DataSourcesGrid.config.spec.mocks.ts`, `DataSourceForceImportModal.spec.mocks.tsx`, and `DataSourcesGrid.spec.mocks.tsx`.

### Option C — Root `__mocks__/` plus `jest.setup.js` for global node_modules stubs

Global stubs for third-party packages that every spec should share live in `frontend/__mocks__/` (Jest's [manual-mocks convention](https://jestjs.io/docs/manual-mocks)), and `frontend/jest.setup.js` opts the shared ones in once with `jest.mock(...)`. Specs should not repeat those calls.

Currently enabled globally (via `frontend/jest.setup.js` + `frontend/__mocks__/`):
- `@swo/design-system/utils`

Available as root manual mocks, but **not assumed globally active**:
- `@mpt-extension/sdk`
- `react-router-dom`
- `react-i18next`

Pattern for pass-through mocks:

```tsx
// frontend/__mocks__/react-router-dom.tsx
const actual = jest.requireActual("react-router-dom");

module.exports = {
  ...actual,
  Link: ({ children }: { children: ReactNode }) => <>{children}</>,
};
```

**When to add a file here:**
- The mock is a third-party (node_modules) package
- Every spec should see the same shape — no per-spec variation
- Reader ambiguity is acceptable (the mock is invisible from the spec file)

**When NOT to use root `__mocks__/`:**
- **User modules with aliased paths** (`~shared/…`, `~organizations/…`) — root `__mocks__/` doesn't reach them. Keep those in `jest.setup.js`, or extract per-spec via Option A/B.
- **Feature-local mocks** — never a good fit; use Option A or Option B.
- **Mocks with per-spec spy assertions** — the invisible global application makes the spy source hard to trace. Use Option A or Option B when specs assert on `.mock.calls`.

### Option D — Jest's `__mocks__/` sibling for individual user modules

Same convention but for user modules: place `<module>.tsx` inside a `__mocks__/` folder next to the real file. Requires opt-in per spec via `jest.mock('./module')` with **no factory**.

Not used in this repo — the shared surface is small enough that Option A (`~test-utils/mocks/`) and Option B (per-spec sibling) cover every case with better spec-side visibility.

### What NOT to share

Feature-local mocks with **small preludes** (a single sibling component or one hook) belong inline in the spec. Once the prelude grows past ~20-30 lines, touches more than 2-3 mocked modules, *or* the spec has more mock setup than actual tests visible above the fold, use **Option B** (per-spec sibling helper) — that keeps the setup near the spec without cluttering it.

Only reach for **Option A** (`~test-utils/mocks/`) when the mock will be imported by two or more specs.

## Testing Patterns

### Grid Components (thin wrappers)
- Mock `@swo/design-system/grid` (`Grid`, `useGridAsync`, `GridCellSimple`)
- Mock the co-located `*.config` module and stub `useGridConfig` return with `silentRefresh`, `refresh`, `onEvent`, `columns`, `fields`
- If the wrapper wires row actions (e.g. force-import modal) — capture the `onAction` callback via `mockUseGridConfig.mock.calls[0][1]`, invoke inside `act(() => ...)`, assert modal props changed

### Details Container
- Mock the child Details component
- Mock the API hook with `get` returning a resolved value
- Provide `QueryClientProvider` + `MemoryRouter` with route params

### Hooks
- `renderHook(() => useHook())` from `@testing-library/react`
- For context-dependent hooks (`useOrganizationContext`, react-query hooks), pass a `wrapper`
- For factory hooks that return functions (`useActionOptions`, `useAsyncOptions`), capture the returned function and assert its output for representative inputs

### Actions
- Mock API hooks and entity hooks
- Mock `useConfirm` from `@swo/design-system/modal`
- Use `userEvent.click()` for interactions
- `await waitFor(...)` for async assertions

## Scope of a unit test

### Test in unit tests
- The code under test's own branching on inputs (`null`, `undefined`, missing, role, feature flag)
- Error paths the code under test itself owns (React Query hooks that expose `error`, action components that catch)
- Memoization boundaries when the `useMemo` dep list is non-trivial
- Callback wiring (capture the passed callback, invoke, assert side-effect)

### Don't test in unit tests
- **Empty-list rendering when Grid is mocked.** The mock's HTML is identical regardless of `data.length`. Only test the empty case when the code under test has explicit `if (data.length === 0)` branching.
- **Translation keys.** `useTranslation` and `useFixedT` are identity-mocked in `jest.setup.js`; asserting keys tests the mock, not the code under test. Use i18n extraction/lint for missing keys; use e2e for translated-text assertions.
- **Third-party library internals** (React Query cache, RQL parser output).
- **Every prop forwarded to a mocked child.** Assert the ones that carry semantic meaning; skip the passthrough noise.

### Null / missing input coverage

For any input that can be `null`/`undefined` at runtime, add one test with the missing value:
- Column cells that read nullable relations (`item.parent?.name`) — one `renderColumnCell` test with the field set to `null`
- Context hooks (`useOrganizationContext`) that can return `undefined` — one `mockReturnValue(undefined)` test
- Route params — one `renderWithRouter` call with the param absent

## AAA Pattern

Follow **Arrange-Act-Assert** strictly:
- No `if` statements or branching in tests
- Use `it.each` / `describe.each` for parameterized tests (fields ↔ column mapping is a great case)
- Prefer setup functions / `beforeEach` over inline mocks
- Use `mockFn.mock.lastCall![i]` for "last invocation" assertions (cleaner than `.calls[len-1]`)

## Canonical spec file layout

Every spec should follow the same top-to-bottom order — makes scanning across specs frictionless.

```
1. imports (test-library → aliases → spies from .spec.mocks → SUT)
2. constants / local types used by tests (COLUMN_FIELDS, NO_VALUE, Controller type)
3. inline `jest.mock` calls + local `mock*` spies (only if no .spec.mocks sibling)
4. helper functions (primeController, factory helpers)
5. describe(...)
```

If the prelude at step 3 grows past ~20-30 lines, spans more than 2-3 mocked modules, or reads like a "mock wall", extract it to a `<file>.spec.mocks.ts[x]` sibling (Option B). The spec then keeps only steps 1, 2, 4, 5 — which reads like actual test code, not "mock wall then tests".

## Reference Example

See `frontend/src/features/organizations/details/data-sources/*.spec.tsx` for the canonical patterns:
- `DataSources.spec.tsx` — container + `MemoryRouter` + child mock; small inline prelude (no sibling helper)
- `DataSourcesGrid.spec.tsx` + `DataSourcesGrid.spec.mocks.tsx` — thin Grid wrapper + extracted sibling helper once the prelude stopped being trivial
- `DataSourcesGrid.config.spec.tsx` + `DataSourcesGrid.config.spec.mocks.ts` — large prelude extracted to sibling helper (Option B); spec imports spies
- `force-import-modal/DataSourceForceImportModal.spec.tsx` + `DataSourceForceImportModal.spec.mocks.tsx` — same pattern, `.tsx` sibling because factories return JSX

## References

- `./references/testing-conventions.md` — Full conventions
- `./references/test-quick-reference.md` — 1-page cheat sheet
- `./references/troubleshooting.md` — Common issues (design-system paths, `@mpt-extension/sdk`, TextEncoder, transformIgnorePatterns)

