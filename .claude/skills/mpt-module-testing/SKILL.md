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

```text
// ✅ Correct — matches actual imports in this repo
jest.mock("@swo/design-system/grid", () => ({
  Grid: (_props: unknown) => null,
  useGridAsync: jest.fn(),
  GridCellSimple: ({ children }: { children?: unknown }) => children,
}));

// ❌ Wrong — no source file imports "@swo/grid"
jest.mock("@swo/grid", () => ({ ... }));
```

Return only the runtime exports the code under test actually uses at runtime; type-only exports are erased by SWC and don't need to be present.

### Prefer source-exported types in shared mocks and test utils

When a shared mock or utility mirrors a component or helper from app code, prefer the **same source-exported types** over handwritten prop shapes.

- Use `import type` so the alignment is compile-time only.
- Prefer `Pick<...>` when the mock only touches a subset of props.
- This rule is strongest for `frontend/src/test-utils/mocks/` and `frontend/src/test-utils/` helpers.
- Don't force it on tiny one-off inline mocks if a local shape is clearer.

```text
import type { GridCellDateProps } from "~shared/components/grid/GridCellDate";
import type { GridCellCurrencyProps } from "~shared/components/grid/GridCellCurrency";

type MockGridCellCurrencyProps = Pick<GridCellCurrencyProps, "value" | "currency">;

export const mockGridCellDate = {
  GridCellDate: ({ value }: GridCellDateProps) => String(value),
};

export const mockGridCellCurrency = {
  GridCellCurrency: ({ value, currency }: MockGridCellCurrencyProps) =>
    `${value}|${currency}`,
};
```

For components whose props are not exported, prefer `ComponentProps<typeof Component>` (or a `Pick<>` subset of it) over re-declaring the prop contract by hand.

### Type `jest.fn()` spies with the real signature

Untyped `jest.fn()` returns `jest.Mock<any, any>`, so `mockReturnValue({ ... })` and `.mock.lastCall![0]` accept any shape. Cast each spy to the real signature so drift (rename, param removal, added return field) surfaces at compile time instead of runtime.

```text
// hook mock — reuse the real hook's signature
import type { useUserRole } from "~shared/hooks/useUserRole";
export const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;

// method on an object returned by a hook
import type { useOrganizationsApi } from "~organizations/api";
type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;
export const mockListOrganizationDataSources = jest.fn() as jest.MockedFunction<
  OrganizationsApi["listOrganizationDataSources"]
>;

// component prop-capture spy — reuse the component's props type
import type { ComponentProps } from "react";
import type { Modal } from "~shared/components/modal/Modal";
type MockModalProps = ComponentProps<typeof Modal>;
export const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;

// function returned FROM a hook (`useActionOptions` returns a fn)
import type { useActionOptions } from "./hooks/useActionOptions";
export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;
```

Related: when the factory wraps a spy with a spreader, prefer `Parameters<typeof realFn>` over `...args: unknown[]` — same drift signal for the call site:

```text
jest.mock("../hooks/useForceImportController", () => ({
  useForceImportController: (...args: Parameters<typeof useForceImportController>) =>
    mockUseForceImportController(...args),
}));
```

**Generic hooks** — `jest.MockedFunction<typeof genericHook>` instantiates every generic to its default (`unknown`, `DefaultError`, `QueryKey`, …), so the return-shape check happens against defaults, not the caller's instantiation. Either accept the caveat (still catches signature-level drift) or leave the spy untyped for hooks like `useReactQueryRqlGrid`. The one in `DataSourcesGrid.config.spec.mocks.ts` is intentionally left untyped for this reason.

**Partial fixtures.** Once spies are typed, `mockReturnValue({ currency: "USD" })` fails when the real return type has more required fields than the test actually reads. Two acceptable escapes, in order of preference:

1. Provide the missing fields with realistic defaults (best when there are only 1–2 gaps).
2. Cast the stand-in: `mockReturnValue({ currency: "USD" } as OrganizationRead)` or `as unknown as ReturnType<typeof useX>()`. Keep the cast tight to the mock call so a reader sees "this is a partial stand-in" — don't `as any` the whole spy or blanket-widen the return type.

**Optional callbacks captured from `.mock.lastCall`.** Reading an optional prop off a typed spy (`mockUseGridAsync.mock.lastCall![0].onEvent`) yields `Callback | undefined`. When the code under test unconditionally wires it up, use a non-null assertion at the read site (`.onEvent!`), not `?.()` at every call — the assertion doubles as documentation ("we expect this to be present") and stays honest if the source ever stops wiring it.

Applied examples in this repo:

- `frontend/src/features/organizations/details/data-sources/DataSourcesGrid.config.spec.mocks.ts` — hook / API-method / returned-function spies typed via `jest.MockedFunction`
- `frontend/src/features/organizations/details/data-sources/DataSourcesGrid.spec.mocks.tsx` — `mockUseGridConfig` typed as `jest.MockedFunction<typeof useGridConfig>`; component-capture spy typed via `ComponentProps`
- `frontend/src/features/organizations/details/data-sources/force-import-modal/DataSourceForceImportModal.spec.mocks.tsx` — every component-capture spy typed to its `ComponentProps<typeof …>`
- `frontend/src/test-utils/mocks/designSystemGrid.tsx` — shared spies (`mockGridProps`, `mockUseGridAsync`, `buildRqlQuery`) typed to the source signatures

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

### `npm test` runs jest + tsc + prettier + eslint in parallel

`@swc/jest` deliberately skips type-checking to stay fast, so drift in typed mock spies (`jest.MockedFunction<typeof …>` vs. the real signature) only surfaces at `tsc` time. To keep the local feedback loop tight, `npm test` runs four checks in parallel via `npm-run-all --parallel --continue-on-error --print-label`:

- `test:unit` — the raw jest invocation (still available on its own for tight-loop debugging)
- `typecheck` — `tsc --noEmit`
- `format:check` — `prettier --check`
- `lint` — `eslint`, includes spec-scoped jest / testing-library / jest-dom rules (see below)

`--continue-on-error` means all four complete every run — you see every failure class at once instead of iterating.

### Spec-scoped ESLint rules (jest / testing-library / jest-dom)

`eslint.config.mjs` has a dedicated block for spec files (`**/*.spec.{ts,tsx}`, `**/*.spec.mocks.{ts,tsx}`, `src/test-utils/**/*`, `jest.setup.js`) that enables the recommended rulesets from three plugins:

- `eslint-plugin-jest` — `no-disabled-tests`, `no-focused-tests`, `expect-expect`, `valid-title`, `no-standalone-expect`, `no-conditional-expect`, etc.
- `eslint-plugin-testing-library` (`flat/react` config) — `prefer-screen-queries`, `no-container`, `no-node-access`, `await-async-utils`, etc.
- `eslint-plugin-jest-dom` — `prefer-in-document`, `prefer-to-have-text-content`, etc.

App code is not touched by these rules. Two patterns to internalise:

- **Use `screen.getBy*`, don't destructure from `render()` result.** The plugin flags `const { getByTestId } = render(...)` — use `render(...)` then `screen.getByTestId(...)` at the assertion site. Same applies to shared helpers like `renderColumnCell` that wrap `render` and return the RTL result.
- **Prefer `toHaveTextContent(...)` over `.textContent === …`.** Jest-dom's matcher gives better diffs and normalises whitespace; `expect(el.textContent).toBe(...)` gets flagged.

### `.spec.mocks` imports must load before the source under test

`jest.mock(...)` calls inside a `.spec.mocks` sibling only fire when that sibling is imported. If the source-under-test import is placed *above* the sibling import, the real modules resolve first and the mocks never take effect — every dependency graph the source touches leaks in ("No QueryClient set", `Cannot destructure property … of undefined`, etc.).

Prettier's sort-imports plugin used to alphabetize `./X.config` before `./X.config.spec.mocks`, which silently broke every spec that extracted its prelude. `frontend/.prettierrc.json` now has a dedicated group for `.spec.mocks` siblings that sits *before* the general `^[./]` group:

```text
"importOrder": [
  ...,
  "^~(.*)$",
  "^[./].*\\.spec\\.mocks(\\.[a-z]+)?$",
  "^[./]"
]
```

Keep this ordering when adding new import-order rules. Never manually swap the two imports back — running `npm run format` will restore them.

### Shared test environment hardening

Keep environment-wide fixes in `frontend/jest.setup.js`; don't patch jsdom gaps in individual specs.

- Add browser API stubs once at the global level when jsdom lacks them.
- Keep root manual mocks for third-party modules that should be shared by every spec.
- Keep shared mock helpers source-typed (`import type`, `Pick<>`, `ComponentProps<typeof ...>`) so they stay aligned with app code.

### Mirror tsconfig aliases in `jest.config.js` `moduleNameMapper`

`tsconfig.json` `paths` and `jest.config.js` `moduleNameMapper` are two separate resolvers — a new alias in tsconfig does not automatically resolve at test time. When you add or rename an alias, mirror it in both places or specs importing through the alias will fail with `Cannot find module '~foo/…'`.

Currently mapped in both: `~api`, `~app`, `~features`, `~fixes`, `~organizations`, `~entitlements`, `~shared`, `~i18n`, `~test-utils`.

### Never Mock
- `react` or `react-dom` (or `react-dom/client`) — bootstrap files that call `createRoot` don't belong in unit tests; cover them via e2e.
- The full `react-router-dom` module in a spec-specific factory (use `MemoryRouter` + `Routes` + `Route` for route params — don't stub `useParams`)

## Gotchas

### Grid column cells with `<Link>` need a router mock

`renderColumnCell` from `~test-utils` wraps `render(...)` without a router. Grid columns whose `cell` renders `<Link>` (e.g. an entity name that links to a detail page) crash with `Cannot destructure property 'basename' of React.useContext(...) as it is null.`

Fix: opt into the root `__mocks__/react-router-dom.tsx` mock's `Link` override in the spec (or the `.spec.mocks` sibling):

```text
jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: { children?: ReactNode }) => <>{children}</> };
});
```

The root `__mocks__/react-router-dom.tsx` is intentionally NOT globally applied so route-param tests keep the real router runtime; opt in per-spec when the code-under-test uses `<Link />` in isolation.

Applied examples: `frontend/src/features/organizations/list/hooks/useColumns.spec.tsx`, `frontend/src/features/entitlements/list/EntitlementsGrid.config.spec.mocks.tsx`.

### Overriding the global `@swo/design-system/utils` mock **replaces** it

The global manual mock at `__mocks__/@swo/design-system/utils.tsx` spreads `...actual` and overrides `DisplayValue` / `useLocalisation` / `useDesignSystemOptions`. If a spec adds its own `jest.mock("@swo/design-system/utils", () => ({ … }))`, it fully **replaces** the global mock — `NO_VALUE` becomes `undefined`, `useLocalisation` is gone, and unrelated tests break with empty text content or undefined-destructure errors.

Two safe patterns:

1. **Re-supply every export the code-under-test touches** (simplest for scoped mocks):
   ```text
   jest.mock("@swo/design-system/utils", () => ({
     NO_VALUE: "—",
     DisplayValue: ({ value }: { value?: unknown }) => <>{value ?? ""}</>,
   }));
   ```

2. **Extend the global mock via `requireActual`** (best when you want everything the global exposes plus one override):
   ```text
   jest.mock("@swo/design-system/utils", () => {
     const actual = jest.requireActual("@swo/design-system/utils");
     return { ...actual, DisplayValue: ({ value }) => <>{value}</> };
   });
   ```

Symptoms of a silent override: highlight-value spans render empty, or `NO_VALUE` fallbacks appear as literal `undefined` in text content.

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
```text
renderWithRouter(componentUnderTest, {
  initialUrl: "/organizations/org-123",
  routePath: "/organizations/:organizationId",
});
```

**React Query:**
```text
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});
const wrapper = createQueryClientWrapper();
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

```text
// src/test-utils/mocks/designSystemGrid.tsx
import type { ComponentProps } from "react";
import type { Grid, GridCellSimple, UseAsyncGridConfig } from "@swo/design-system/grid";

type MockGridProps = ComponentProps<typeof Grid>;
type MockGridCellSimpleProps = Pick<ComponentProps<typeof GridCellSimple>, "children">;

export const mockGridProps = jest.fn() as jest.MockedFunction<(props: MockGridProps) => void>;
export const mockUseGridAsync = jest.fn() as jest.MockedFunction<
  (config: UseAsyncGridConfig<object>) => unknown
>;

export const mockDesignSystemGrid = {
  Grid: (props: MockGridProps) => {
    mockGridProps(props);
    return null;
  },
  GridCellSimple: ({ children }: MockGridCellSimpleProps) => children,
  useGridAsync: (config: UseAsyncGridConfig<object>) => mockUseGridAsync(config),
};
```

```text
// Feature.spec.tsx
import { mockDesignSystemGrid, mockGridProps } from "~test-utils/mocks/designSystemGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
```

The imported spies (`mockGridProps`, `mockUseGridAsync`) are the same instances the mock factory references, so `mockReturnValue` / `.mock.calls` in the test drive what the code-under-test sees. `clearMocks: true` in `jest.config.js` resets them between tests automatically.

Existing shared mocks:
- `~test-utils/mocks/designSystemGrid` — `Grid`, `GridCellSimple`, `useGridAsync`, `buildRqlQuery`
- `~test-utils/mocks/entityReferenceCell` — `EntityReferenceCell`
- `~test-utils/mocks/sharedGridCells` — `CustomIcon`, `GridCellCurrency`, `GridCellDate`, `GridCellDynamicActions`

### Type-Safe Shared Test Utilities

When you add or refactor helpers in `frontend/src/test-utils/` or `frontend/src/test-utils/mocks/`, prefer the same type the source code exports.

- Prefer `import type` from the app component/hook when it exports props or return types
- Prefer `Pick<...>` when the helper only touches part of the source contract
- Prefer `ComponentProps<typeof Component>` when the source prop type is not exported
- Use local `unknown` / `as unknown as ...` bridges only for intentional fixture gaps or runtime-only test inputs

Applied examples in this repo:

- `frontend/src/test-utils/mocks/designSystemGrid.tsx` — grid and cell mock props follow exported `Grid` / `GridCellSimple` component types
- `frontend/src/test-utils/mocks/entityReferenceCell.tsx` — uses `ComponentProps<typeof EntityReferenceCell>`
- `frontend/src/test-utils/mocks/sharedGridCells.tsx` — uses `GridCellCurrencyProps`, `GridCellDateProps`, and `GridCellDynamicActionsProps`
- `frontend/src/test-utils/renderCell.tsx` — uses `Pick<GridColumnDefinition<T>, "cell" | "name">`
- `frontend/src/test-utils/columnByName.ts` — uses `Pick<GridColumnDefinition<object>, "name">`
- `frontend/src/features/organizations/details/data-sources/DataSources.spec.tsx` — container mock props use `ComponentProps<typeof DataSourcesGrid>`
- `frontend/src/features/organizations/details/data-sources/force-import-modal/DataSourceForceImportModal.spec.mocks.tsx` — modal, date picker, notifications, text, and in-page highlight mocks use source-derived component props

### Option B — Per-spec sibling helper (`<file>.spec.mocks.ts[x]`)

For a spec whose prelude of local `jest.mock` + `mock*` spies exceeds ~20-30 lines, touches more than 2-3 mocked modules, or simply reads like a “mock wall”, extract the entire prelude into a **sibling file next to the spec**: `<Feature>.spec.mocks.ts` (or `.tsx` if a factory returns JSX). The spec then imports only the spies and stays focused on setup helpers + `describe`.

```text
// DataSourcesGrid.config.spec.mocks.ts
import type { useOrganizationContext } from "~organizations/providers/OrganizationsProvider";
import type { useUserRole } from "~shared/hooks/useUserRole";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";

// Re-export shared spies the spec asserts against
export { mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

// Local spies — typed to the real hook signature so mockReturnValue is checked
export const mockUseOrganizationContext = jest.fn() as jest.MockedFunction<
  typeof useOrganizationContext
>;
export const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;

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

```text
// DataSourcesGrid.config.spec.tsx
import { renderHook } from "@testing-library/react";

import {
  mockUseGridAsync,
  mockUseOrganizationContext,
  mockUseUserRole,
} from "./DataSourcesGrid.config.spec.mocks";

import { useColumns } from "./DataSourcesGrid.config";

describe("DataSourcesGrid.config", () => { /* ... */ });
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

```text
// frontend/__mocks__/react-router-dom.tsx
const actual = jest.requireActual("react-router-dom");

module.exports = {
  ...actual,
  Link: ({ children }: { children: ReactNode }) => children,
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
- Mock the co-located `*.config` module and stub `useGridConfig` return with the props the wrapper actually spreads into `<Grid />` (typically `silentRefresh`, `refresh`, `onEvent`). Once `mockUseGridConfig` is typed as `jest.MockedFunction<typeof useGridConfig>`, partial stubs need a `as unknown as ReturnType<typeof useGridConfig>` bridge — see `DataSourcesGrid.spec.tsx` for the canonical shape
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

### Modals (callback-capture pattern)

Modal specs mock the shared `Modal` component with a capture spy, then invoke the captured `onSubmit`/`onCancel` inside `act(...)` to drive the modal's flow:

```text
type MockModalProps = ComponentProps<typeof Modal>;
const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;

jest.mock("~shared/components/modal/Modal", () => ({
  Modal: (props: MockModalProps) => {
    mockModal(props);
    return <div data-testid="modal">{props.children}</div>;
  },
}));

// Drive submit — await when the source chains .then(() => onSuccess?.())
await act(async () => {
  await mockModal.mock.lastCall![0].onSubmit();
});

// Drive cancel — optional-chain the callback since Modal treats onCancel as optional
act(() => mockModal.mock.lastCall![0].onCancel?.());
```

Rules of thumb:
- Assert only the props with real behavioral meaning: `isOpen`, `isSubmitting`, `isSubmitDisabled`, the entity payload, the wired callbacks. Don't over-assert every forwarded prop.
- One test per guard-clause: `"submit is a noop when entitlement is null"`, `"submit is a noop when organizationId is null"`.
- Use `mockModal.mock.lastCall![0]` for "final render" state (cleaner than `.calls[len-1]`).

Canonical examples: `DeleteEntitlementModal.spec.tsx`, `TerminateEntitlementModal.spec.tsx`, `UserMakeAdminModal.spec.tsx`, `DeleteOrganizationModal.spec.tsx`, `EditOrganizationModal.spec.tsx`, `CreateUserModal.spec.tsx`.

### React Query mutation controllers

Controllers built on `useMutation` need the real query client (`createQueryClientWrapper()`) so `useMutation`'s state transitions fire. Mock the API method the mutation calls, mock `useErrorDetails.getErrorMessage`, then drive:

```text
async () => {
  mockDeleteEntitlement.mockResolvedValueOnce(OK_RESPONSE);
  const onClose = jest.fn();
  const { result } = renderController(onClose);

  await act(async () => {
    await result.current.remove(entitlement);
  });

  await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
};
```

Rejection path — `mutateAsync` **re-throws** even though `onError` handles it, so wrap the invocation:

```text
async () => {
  const failure = new Error("boom") as AxiosError;
  mockGetErrorMessage.mockReturnValue("readable failure");
  mockDeleteEntitlement.mockRejectedValueOnce(failure);
  const { result } = renderController();

  await act(async () => {
    await expect(result.current.remove(entitlement)).rejects.toBeDefined();
  });

  await waitFor(() => expect(result.current.error).toBe("readable failure"));
  expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
};
```

Without the `rejects.toBeDefined()` wrapper (or `.catch(() => undefined)`), the test still passes but Node prints an unhandled-promise warning that pollutes the run.

Canonical examples: `useEntitlementController.spec.tsx`, `useDeleteOrganizationController.spec.tsx`, `useForceImportController.spec.tsx`.

### Wizard steps vs. form controllers — two patterns

These look similar but split cleanly:

**Wizard steps** (`AffiliateStep`, `DataSourceStep`, `ReviewStep`, `SummaryStep`) read live form state via `useWatch` / `useFormState` / `getValues`. Render them inside a real `<FormProvider {...useForm()}>` and inject stub `trigger` / `setValue` when needed:

```text
function renderStep() {
  const trigger = jest.fn().mockResolvedValue(true);
  function Wrapper() {
    const methods = useForm<AddWizardForm>();
    methods.trigger = trigger as unknown as typeof methods.trigger;
    return (
      <FormProvider {...methods}>
        <AffiliateStep />
      </FormProvider>
    );
  }
  render(<Wrapper />);
  return { trigger };
}
```

**Form controllers** (`useUserFormController`, `useOrganizationsController`) wire `handleSubmit(onSubmit)` into a mutation. Mock `useXForm` entirely and inject a fake `handleSubmit` that immediately calls the callback with a valid payload — that way the spec drives the mutation without needing to satisfy zod validation:

```text
const validPayload: AddUserForm = { email: "user@example.com", display_name: "User" };
const mockHandleSubmit = jest.fn(
  (cb: (data: AddUserForm) => Promise<void> | void) => () => Promise.resolve(cb(validPayload)),
) as unknown as FormReturn["handleSubmit"];

jest.mock("./useAddUserForm", () => ({
  useAddUserForm: () => ({ handleSubmit: mockHandleSubmit, control: {}, reset: mockReset }),
}));
```

Canonical examples: `AffiliateStep.spec.tsx` (real FormProvider), `useUserFormController.spec.tsx` (mocked `useAddUserForm`).

## When NOT to write a unit test

Some files don't earn a spec. Skipping them keeps the suite lean and honest.

- **Bootstrap glue** (`entries/StandaloneRoot.tsx`): calling `createRoot` and rendering the app tree is the file's whole job. Testing it requires mocking `react-dom/client`, which violates the "never mock React/React DOM" rule. E2e covers this instead.
- **Barrel files** (`api/index.ts`, `app/layouts/index.ts`): re-exports only. TypeScript already enforces the surface.
- **Type-only modules** (`api/model.ts`): no runtime behaviour to exercise.
- **Path aggregators that only re-export** (`app/paths.ts` used to be a re-export of feature paths): identity checks are change-detectors — if the re-export breaks, the compile does too.
- **Path constant *literals*** (`PARAMS.entitlementId = "entitlementId"`): the assertion just repeats the source string. Keep the URL *builders* (`PATHS.detail("x") === "/x/..."`) — those protect the URL contract with the backend.

If you're tempted to add a spec, ask: *would a plausible bug in this file survive a passing test?* If the failure mode is only "the source string changed", the test is a change-detector — delete it.

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

## Readable Test Names

Keep test names short, specific, and behavior-focused.

- Prefer names that describe the observable result, not the implementation.
- Include the important scenario or input when it matters (`missing route param`, `role = admin`, `null value`).
- Use `describe` for the subject under test and `it` for the behavior being verified.
- If a test name needs multiple `and`s, split it into separate tests.

### Test name anti-patterns

Grep for these regularly — if any hit, the name is a candidate for rewrite:

```bash
grep -rEn "successfully|correctly|properly|works fine|should |verifies|ensures|makes sure|the correct|the right|the expected|handles|processes|test case" src/**/*.spec.{ts,tsx}
```

Common rewrites:

| Anti-pattern | Rewrite |
|---|---|
| `"renders the correct X"` | `"renders %s at index=%i"` with a named parameterized column |
| `"notifies parent about X"` | `"passes X to useNotifyParentChildModal"` |
| `"initialises Y with Z"` | `"passes Z to Y"` |
| `"returns X in the expected order"` | `"returns X in fixed order"` |
| `"exposes X as a list with the expected options"` | `"exposes X as a list with a, b, c options"` |
| Internal handler in `it()` (`"closeWizard calls onClose"`) | Observable trigger (`"Wizard onClose reports success=false"`) |
| `"successfully X"` / `"correctly X"` | Just `"X"` — no filler |

Rule of thumb: **subject → verb → observable outcome**. If you can't describe the outcome, the test may not be worth keeping.

## Tests to delete on sight

Some spec patterns test framework internals or repeat source literals — deleting them costs no coverage. Grep for these during review:

- **`"returns a memoized … stable across re-renders"`** / **`"returns a stable callback across renders"`** — tests React's `useMemo` / `useCallback` internals. If they broke, the app would still work; only perf profiling would notice. Delete.
- **Change-detector path literal assertions** (`expect(PARAMS.x).toBe("x")`, `expect(SEGMENTS.idParam).toBe(":x")`) — the assertion repeats a literal in the source. Change one, change both. Delete; keep the URL *builder* tests.
- **Re-export identity checks** (`expect(PATHS.organizations).toBe(organizations)`) — TypeScript's job.
- **"Not called by default" negative assertions** where the trigger isn't wired in the test — mirrors the source shape without proving anything about behaviour. Especially common in wizard/controller specs that admit via comment: *"can't drive this from the outside"*.
- **Duplicated modal wiring tests** — one `"Modal onClose bridges to onClose prop"` and one `"closeWizard calls onClose"` in the same file usually exercise the same code path. Keep the one framed in user terms.
- **Docstrings above `it(...)`** — `it("…")` is the docstring; JSDoc above it is noise that drifts.

If a test doesn't protect a user-visible behaviour, a business rule, a regression, an edge case, or an integration boundary — reconsider whether it should exist.

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

## Final refactor pass after finishing test work

Once the spec is green, review the **whole touched frontend unit-test surface** before considering the job done.

Look across the edited `*.spec.tsx` / `*.spec.ts` files, sibling `.spec.mocks` files, and `frontend/src/test-utils/` to find patterns that should be shared instead of copied.

Typical extraction candidates:

- repeated render wrappers or provider setup
- repeated typed mock factories / prop-capture spies
- repeated domain test data builders / factories
- repeated callback-invocation helpers or assertion helpers
- the same module mock shape copied across multiple specs

Prefer extracting only patterns that appear in two or more places or clearly improve readability. Keep one-off setup inline when extraction would hide the behavior under test or make the spec harder to read.

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

