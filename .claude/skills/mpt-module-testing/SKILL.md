---
name: mpt-module-testing
description: Write unit tests for MPT frontend modules. Jest + @testing-library/react + @swc/jest (CJS). Use for testing Grid components, Details containers, entity hooks, action components, wizard components, API hooks. Layers code recipes and spec-file layout on top of the project's testing convention doc.
---

# MPT Module Testing

**Canonical rules live in the active project's `docs/conventions/testing.md`** (ffc-extension: [`docs/conventions/testing.md`](../../../docs/conventions/testing.md)) — stack facts, file naming, coverage floor, mocking rules (DS full-path, no-spread, pre-mocked modules, never-mock list, utils override gotcha), typed-spy table + source-type derivation, test-utils inventory + promotion threshold, spec-scoped ESLint, "when not to write a unit test", test-name style, and "patterns to delete on sight". **That doc wins on drift.**

Baseline frontend conventions (path aliases, DS subpath imports, derived TS types, Fast Refresh, verify commands) are in **`mpt-frontend-standards`**. Concrete project bindings (`test-utils` paths, factories, shared mock inventory, entity route helpers) are in the active project's `*-local` skill — in ffc-extension that's [`ffc-local`](../ffc-local/SKILL.md).

This skill layers Claude-level recipes on top: spec file layout, how a Grid wrapper spec is driven, how to capture modal callbacks, how to test a mutation controller, where a typed spy lives in a `.spec.mocks` sibling, and a few gotchas the convention doc doesn't cover.

## Spec file layout

```
1. imports (test-library → aliases → spies from .spec.mocks → source under test)
2. constants / local types
3. inline jest.mock + local mock* spies (only if no .spec.mocks sibling)
4. helper functions
5. describe(...)
```

Extract to `<file>.spec.mocks.ts[x]` when step 3 grows past ~20-30 lines or spans 3+ mocked modules. Canonical examples typically live under a nested feature folder — in ffc-extension the reference set is at `frontend/src/features/organizations/details/data-sources/`: small inline prelude (`DataSources.spec.tsx`), grid wrapper with sibling helper (`DataSourcesGrid.spec.tsx` + `.spec.mocks.tsx`), large prelude fully extracted (`DataSourcesGrid.config.spec.tsx` + `.spec.mocks.ts`). The project's `*-local` skill lists the canonical example set for the current project.

## Test wrappers

Router (for `useParams` — don't mock `react-router-dom`):

```text
renderWithRouter(componentUnderTest, {
  initialUrl: "/organizations/org-123",
  routePath: "/organizations/:organizationId",
});
```

Entity detail routes — the project should expose one helper per entity (ffc-extension ships `renderWithEntitlementRoute` + `renderWithOrganizationRoute`; see [`ffc-local`](../ffc-local/SKILL.md) for the full list):

```text
renderWithEntitlementRoute(componentUnderTest, {
  id: "ent-123",
  routePath: "/entitlements/:entitlementId/*",
});

renderWithOrganizationRoute(componentUnderTest, {
  id: "org-123",
  routePath: "/organizations/:organizationId/*",
});
```

Use the entity-specific helpers for detail shells and leaf routes instead of repeating IDs and route strings inline.

React Query (real client — needed for `useMutation` state transitions):

```text
const wrapper = createQueryClientWrapper(); // uses { queries: { retry: false } }
const { result } = renderHook(() => useMyHook(), { wrapper });
```

## Shared mock usage pattern

Shared mocks live in the project's `test-utils/mocks/` folder. Each file exports both a **spy** (`mockUseX`) and a **module shape** (`mockXModule`), wired to call the spy:

```text
import { mockDesignSystemGrid, mockGridProps, mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
mockUseGridAsync.mockReturnValue(/* ... */);
```

Both names must start with `mock*` so jest's hoist rule accepts them. The current project's full shared-mock inventory is in its `*-local` skill (ffc-extension: [`ffc-local`](../ffc-local/SKILL.md)).

## Gotchas not in the convention doc

### Grid column cells with `<Link>` need a router mock

`renderCell` from the project's `test-utils` folder renders without a router. Columns whose `cell` uses `<Link>` crash with `Cannot destructure property 'basename' of React.useContext(...) as it is null.`

Opt into the root `react-router-dom` mock's `Link` override:

```text
jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: { children?: ReactNode }) => <>{children}</> };
});
```

The root mock is intentionally NOT global so route-param tests keep the real runtime.

## Testing patterns

### Grid components (thin wrappers)

- Mock `@swo/design-system/grid` (`Grid`, `useGridAsync`, `GridCellSimple`) — use the project's shared mock at `test-utils/mocks/designSystemGrid`.
- Mock the co-located `*.config` and stub `useGridConfig` return with the props the wrapper spreads (`silentRefresh`, `refresh`, `onEvent`). Typed spies need `as unknown as ReturnType<typeof useGridConfig>` for partial fixtures.
- Row-action wiring: capture the `onAction` callback via `mockUseGridConfig.mock.calls[0][1]`, invoke inside `act(...)`, assert modal props changed.

### Container components

- Mock the child Details component.
- Mock the API hook with `get` returning a resolved value.
- Provide `QueryClientProvider` + `MemoryRouter` with route params.
- Two tests: happy path + missing-param path.

### Grid config hooks (`useColumns`, `useFields`, `useAsyncOptions`, `useGridConfig`)

- Mock every peer hook and rendered leaf component.
- Test column order + `fields` mapping (`it.each` is a great fit) and rendered cell output (invoke `column.cell` via `renderCell`).

### Hooks

- `renderHook(() => useHook())` from `@testing-library/react`.
- Context-dependent hooks: pass a `wrapper`.
- Factory hooks returning functions: capture the returned function, assert output for representative inputs.

### Actions

- Mock API hooks, entity hooks, and `useConfirm` from `@swo/design-system/modal`.
- `userEvent.click()` for interactions; `await waitFor(...)` for async assertions.
- When multiple tests in a file repeat the same `const user = userEvent.setup()` arrange step, extract a tiny local helper or shared test util instead of duplicating the setup ceremony.

### Modals (callback capture)

Mock the project's shared `Modal` wrapper (not the raw `@swo/design-system/modal`) with a capture spy, drive its callbacks:

```text
import { mockSharedModal, mockModal } from "~test-utils/mocks/modal";
import { triggerModalSubmit, triggerModalCancel } from "~test-utils";

jest.mock("~shared/components/modal/Modal", () => mockSharedModal);

// ...
await triggerModalSubmit(mockModal);
triggerModalCancel(mockModal);
```

Resolve the shared Modal path and the test-utils path via your project's `*-local` skill.

Rules of thumb:

- Assert only props with behavioural meaning: `isOpen`, `isSubmitting`, `isSubmitDisabled`, the entity payload, wired callbacks.
- One test per guard clause (`"does not call remove when no entitlement is provided"`).
- Use `mockModal.mock.lastCall![0]` for "final render" state.

### React Query mutation controllers

Need the real query client (`createQueryClientWrapper()`) so `useMutation` state transitions fire. Mock the API method, mock `useErrorDetails.getErrorMessage`, drive via `act(async () => await result.current.remove(entity))`.

**Rejection path gotcha:** `mutateAsync` **re-throws** even though `onError` handles it. Wrap invocation in `await expect(...).rejects.toBeDefined()` (or `.catch(() => undefined)`) or Node prints an unhandled-rejection warning that pollutes the run.

### Wizard steps vs. form controllers — two patterns

- **Wizard steps** read live form state via `useWatch` / `useFormState` / `getValues`. Render inside a real `<FormProvider {...useForm()}>` and inject stub `trigger` / `setValue` when needed.
- **Form controllers** wire `handleSubmit(onSubmit)` into a mutation. Mock the form hook entirely and inject a fake `handleSubmit` that immediately calls the callback with a valid payload — bypasses zod validation so the spec drives the mutation directly.

## AAA structure

- No `if` statements or branching in tests.
- `it.each` / `describe.each` for parameterised tests.
- Prefer setup functions / `beforeEach` over inline mocks.
- `mockFn.mock.lastCall![0]` for last-invocation assertions.

## Final pass after finishing test work

Review the whole touched surface (edited specs, sibling `.spec.mocks` files, `src/test-utils/`) for patterns that should be shared instead of copied: render wrappers, typed mock factories, domain factories, callback-invocation helpers, repeated module mock shapes. Extract only patterns appearing in 2+ places or clearly improving readability.

## References

- [`docs/conventions/testing.md`](../../../docs/conventions/testing.md) — canonical rules; wins on drift.
- [`./references/troubleshooting.md`](./references/troubleshooting.md) — common issues (design-system paths, `@mpt-extension/sdk`, TextEncoder, `transformIgnorePatterns`, `column.cell` calling).
