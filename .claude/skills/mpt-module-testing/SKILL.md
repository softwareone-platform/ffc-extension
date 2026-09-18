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

### Pre-Mocked Modules (already in `jest.setup.js` — DO NOT mock again)
- `react-router-dom` — `Link` only; other exports pass through to the real module
- `react-i18next` — `useTranslation` returns identity `t`, `Trans` renders `i18nKey`
- `~shared/hooks/useFixedT` — returns identity function
- `@swo/design-system/utils` — `useDesignSystemOptions`, `useLocalisation`, `DisplayValue`
- `@mpt-extension/sdk` — stubbed with `{ setup, http }` (`{ virtual: true }`; the package ships an ESM-only export, so `require()` cannot resolve it)

Global stubs also live there:
- `TextEncoder` / `TextDecoder` on `globalThis` — jsdom does not provide them natively; `react-router-dom` reaches for them at import time.

### Never Mock
- `react` or `react-dom`
- The full `react-router-dom` module (use `MemoryRouter` + `Routes` + `Route` for route params — don't stub `useParams`)

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

### Option B — Jest's manual mocks (`__mocks__/`)

Use when *every* spec should see the same mock and no per-spec variation is needed. Follow [Jest's manual-mocks convention](https://jestjs.io/docs/manual-mocks):

- **node_modules**: `<projectRoot>/__mocks__/<pkg>.tsx` — auto-applied to every test; no `jest.mock(...)` call needed.
- **User modules**: `__mocks__/<module>.tsx` next to the real file — opt-in via `jest.mock('./module')` with **no factory**.

Trade-off: readers of a spec cannot tell that a `node_modules` mock is in effect (it's auto-loaded). Prefer Option A when the mock exposes spies that specs assert on, or when specs need different shapes. No `__mocks__/` folders exist in this repo today — the shared surface is small enough that Option A is a better fit.

### What NOT to share

Feature-local mocks (a sibling component the spec is exercising, a hook only this feature uses) belong inline in the spec. Extracting them just pushes the reader between files for zero reuse.

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

## AAA Pattern

Follow **Arrange-Act-Assert** strictly:
- No `if` statements or branching in tests
- Use `it.each` / `describe.each` for parameterized tests (fields ↔ column mapping is a great case)
- Prefer setup functions / `beforeEach` over inline mocks

## Reference Example

See `frontend/src/features/organizations/details/data-sources/*.spec.tsx` for the canonical pattern:
- `DataSources.spec.tsx` — container + `MemoryRouter` + child mock
- `DataSourcesGrid.spec.tsx` — thin Grid wrapper + `useGridConfig` mock + modal side-effect via `act()`
- `DataSourcesGrid.config.spec.tsx` — `useColumns` / `useFields` / `useAsyncOptions` / `useGridConfig` with all peer hooks mocked

## References

- `./references/testing-conventions.md` — Full conventions
- `./references/test-quick-reference.md` — 1-page cheat sheet
- `./references/troubleshooting.md` — Common issues (design-system paths, `@mpt-extension/sdk`, TextEncoder, transformIgnorePatterns)
