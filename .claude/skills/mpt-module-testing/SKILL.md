---
name: mpt-module-testing
description: Write unit tests for MPT modules (ffc-extension frontend). Jest + @testing-library/react + @swc/jest (CJS). Use for testing Grid components, Details containers, entity hooks, action components, wizard components, API hooks. Critical rules around design system import paths, pre-mocked modules, and gotchas around @mpt-extension/sdk.
---

# MPT Module Testing (ffc-extension)

Stack: `jest@30` + `@swc/jest` (CJS transform) + `jest-environment-jsdom` + `@testing-library/react@16`. Config in `frontend/jest.config.js`; global setup in `frontend/jest.setup.js`.

Key runtime facts: `clearMocks: true` (no manual resets needed), `testTimeout: 10_000`, `workerIdleMemoryLimit: '512MB'` (heap-sensitive — see Never spread the real design-system module).

## Critical Rules

### File extension

Always `.spec.tsx` (or `.spec.ts` for utilities without JSX). Never `.test.tsx`.

### Coverage floor

Unit-test coverage must always stay above **85%**. If a change drops coverage below that threshold, add meaningful tests or remove low-value assertions before finishing. Prefer behaviour-finding tests over shallow change-detectors when raising coverage.

### Design system: mock the FULL import path

Source imports from `@swo/design-system/[component]`. Mock **that exact path** — `@swo/[component]` (the shortened form from `mpt-vikings-ui`) does not match anything and the mock silently no-ops.

```text
jest.mock("@swo/design-system/grid", () => ({
  Grid: (_props: unknown) => null,
  useGridAsync: jest.fn(),
  GridCellSimple: ({ children }: { children?: unknown }) => children,
}));
```

Return only the runtime exports the code under test uses. Type-only exports are erased by SWC.

### Never spread the real design-system module

`...jest.requireActual("@swo/design-system/grid")` blows the heap. Design-system subpaths pull enormous dependency graphs; the 512MB worker limit will trip. Enumerate the exports you need instead.

### Type `jest.fn()` spies with the real signature

Untyped `jest.fn()` returns `jest.Mock<any, any>` — `mockReturnValue({...})` and `.mock.lastCall![0]` accept anything and drift silently.

Do **not** handwrite component prop contracts in specs or mock helpers when the real source type is available. Prefer `ComponentProps<typeof X>`, `Pick<ComponentProps<typeof X>, ...>`, exported app prop types, or `ReturnType<typeof useHook>` over `type FooProps = { ... }` copies.

| Spy target                                 | Typing                                                           |
| ------------------------------------------ | ---------------------------------------------------------------- |
| Hook                                       | `jest.MockedFunction<typeof realHook>`                           |
| Method on hook's returned object           | `jest.MockedFunction<ReturnType<typeof useApi>["method"]>`       |
| Function returned FROM a hook              | `jest.MockedFunction<ReturnType<typeof useHook>>`                |
| Component prop-capture spy                 | `jest.MockedFunction<(props: ComponentProps<typeof C>) => void>` |
| Generic hook (e.g. `useReactQueryRqlGrid`) | leave untyped — `MockedFunction` collapses generics to defaults  |

When the mock factory wraps a spy with a spreader, use `Parameters<typeof realFn>` (not `...args: unknown[]`) so the call site drifts too:

```text
jest.mock("../hooks/useForceImportController", () => ({
  useForceImportController: (...args: Parameters<typeof useForceImportController>) =>
    mockUseForceImportController(...args),
}));
```

**Partial fixtures** that a typed spy rejects: prefer supplying missing fields with realistic defaults; otherwise cast tight at the call site — `mockReturnValue({ currency: "USD" } as OrganizationRead)`, never `as any` the spy itself.

**Optional callbacks from `.mock.lastCall`**: when the source unconditionally wires the callback, assert once with `!` at the read site (`.onEvent!`) — the assertion documents "we expect this to be present" and stays honest if the source stops wiring it.

### Pre-mocked modules (do not re-mock)

Globally activated in `frontend/jest.setup.js`:

- `@swo/design-system/utils` (root manual mock — passes actual through, overrides `useDesignSystemOptions`, `useLocalisation`, `DisplayValue`)
- `@mpt-extension/sdk` (`{ setup, http }` stubs — ESM-only package, cannot be resolved normally in CJS)
- `~shared/hooks/useFixedT` (identity function)

Global stubs also in `jest.setup.js`: `TextEncoder` / `TextDecoder` (needed at `react-router-dom` import time) and `ResizeObserver` (design-system components expect it).

**Root manual mocks NOT globally active** (opt in per spec):

- `__mocks__/react-router-dom.tsx` — pass-through, overrides `Link`. Route-param tests keep the real runtime by default.
- `__mocks__/react-i18next.tsx` — identity `useTranslation`; `Trans` renders `i18nKey`.

### Never mock

- `react`, `react-dom`, `react-dom/client` — bootstrap files (`createRoot`) are covered by e2e.
- Full `react-router-dom` in a spec-specific factory. Use `MemoryRouter` + `Routes` + `Route` for `useParams`.

### `npm test` runs jest + tsc + prettier + eslint in parallel

SWC skips type-checking, so typed-spy drift only surfaces at the tsc step. `npm test` runs all four via `npm-run-all --parallel --continue-on-error` so every failure class shows on one run.

Run coverage when your change touches branching logic, route composition, or shared test infrastructure. Treat `<85%` as a failed outcome even if the Jest run itself passes.

### Spec-scoped ESLint

`eslint.config.mjs` enables `eslint-plugin-jest` / `-testing-library` / `-jest-dom` on spec globs. Two consequences worth internalising:

- Use `screen.getBy*` — do not destructure from `render()`.
- Use `toHaveTextContent(...)` — not `expect(el.textContent).toBe(...)`.

### `.spec.mocks` siblings must sort before the source under test

`jest.mock(...)` in a `.spec.mocks` sibling fires only when the sibling is imported. If the source-under-test import lands first, real modules resolve before mocks apply. `frontend/.prettierrc.json` has a dedicated import-order group for `.spec.mocks` before the general `^[./]` group — do not reorder.

### Aliases live in two places

`tsconfig.json` `paths` and `jest.config.js` `moduleNameMapper` are separate resolvers. New aliases must be added to both or specs fail with `Cannot find module '~foo/…'`.

## Test wrappers

**Router (for `useParams` — don't mock it):**

```text
renderWithRouter(componentUnderTest, {
  initialUrl: "/organizations/org-123",
  routePath: "/organizations/:organizationId",
});
```

**Entity detail route helpers:**

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

Use these helpers for entitlement/organization detail shells and leaf routes instead of repeating IDs and route strings inline.

**React Query:**

```text
const wrapper = createQueryClientWrapper(); // uses { queries: { retry: false } }
const { result } = renderHook(() => useMyHook(), { wrapper });
```

## Shared test infrastructure

`frontend/src/test-utils/` (exported via `~test-utils`):

- `renderWithRouter`, `renderWithEntitlementRoute`, `renderWithOrganizationRoute`, `createQueryClientWrapper` — provider wrappers
- `renderCell(column, item)` — invoke a Grid column's `cell` function safely (`Pick<GridColumnDefinition<T>, "cell" | "name">`)
- `columnByName(columns, name)` — column lookup
- `triggerModalSubmit(mockModal)` / `triggerModalCancel(mockModal)` — invoke captured Modal callbacks inside `act(...)` (see Modals below)
- `factories/` — `makeAccount`, `makeDatasource`, `makeEmployee`, `makeEntitlement`, `makeOrganization` (typed `Partial<T>`-overlay builders)

Shared mocks live in `src/test-utils/mocks/`. Import both the module and the spies; the spies are the same instances the factory references, so `mockReturnValue` / `.mock.calls` in the test drive what the code under test sees.

```text
import { mockDesignSystemGrid, mockGridProps, mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
```

Current inventory (browse `src/test-utils/mocks/` for exact shapes): `controlledInput`, `designSystemButton`, `designSystemGrid`, `designSystemText`, `entityReferenceCell`, `errorDetails`, `fixedT`, `inPageHighlight`, `inlineErrorNotification`, `modal`, `sharedGridCells`, `sharedGridHooks`, `userRole`, `wizardStep`.

### `useFixedT` mocking

`~shared/hooks/useFixedT` is globally mocked to an identity translator in `jest.setup.js`. When a spec needs deterministic translated output, prefer the shared helper from `~test-utils/mocks/fixedT` instead of hand-writing local translation factories.

```text
import { mockFixedT } from "~test-utils/mocks/fixedT";
import { useFixedT } from "~shared/hooks/useFixedT";

mockFixedT(jest.mocked(useFixedT));
mockFixedT(jest.mocked(useFixedT), (key, params) => `${key}:${params?.code}`);
```

If the code under test imports `./useFixedT` relatively rather than through `~shared/...`, locally mock that module to `jest.fn()` first, then drive it with `mockFixedT(...)`.

### Shared Button mock

Prefer `~test-utils/mocks/designSystemButton` for `@swo/design-system/button` instead of hand-writing a `<button>` factory in each spec.

```text
import { mockButton, mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);
```

Assert only behaviourally relevant props (`children`, `type`, `color`, `isDisabled`, `isBusy`, click wiring) and interact through the rendered `<button>` where possible.

### Type shared mocks from source

When a shared mock or utility mirrors an app component/hook, prefer the source-exported types over handwritten prop shapes.

- `import type` — compile-time only
- `Pick<Props, ...>` when the mock touches a subset
- `ComponentProps<typeof Component>` when the source doesn't export its props
- Keep local handwritten types only for true test-harness state that the app does not export (for example a tiny `FormValues` object or a one-off callback payload used only inside the spec).

```text
import type { ComponentProps } from "react";
import type { Grid } from "@swo/design-system/grid";

type MockGridProps = ComponentProps<typeof Grid>;
export const mockGridProps = jest.fn() as jest.MockedFunction<(props: MockGridProps) => void>;
```

## Mock organisation: three options

**Option A — shared factory (`~test-utils/mocks/`).** For mocks reused by 2+ specs. Constraints: exports must start with `mock*` (Jest hoist rule), static imports only (ESLint bans `require(...)` in factories).

**Option B — per-spec sibling `<File>.spec.mocks.ts[x]`.** Extract when the prelude exceeds ~20-30 lines, touches 3+ mocked modules, or reads like a "mock wall". Same directory as the spec so relative paths inside `jest.mock` resolve identically. `jest.mock` calls in the sibling apply to the spec's run because Jest registers them in the per-test module registry as soon as the file is imported.

**Option C — root `frontend/__mocks__/`.** Only for third-party (`node_modules`) packages that every spec should see identically. User modules with aliased paths (`~shared/…`) cannot go here — root `__mocks__/` doesn't reach them; put those in `jest.setup.js` or extract via A/B.

**Keep inline** when the prelude is small (<20 lines) and stays close to the assertions.

Canonical example set: `frontend/src/features/organizations/details/data-sources/`

- `DataSources.spec.tsx` — container + `MemoryRouter` + child mock; small inline prelude
- `DataSourcesGrid.spec.tsx` + `.spec.mocks.tsx` — thin Grid wrapper with extracted sibling helper
- `DataSourcesGrid.config.spec.tsx` + `.spec.mocks.ts` — large prelude extracted; spec imports spies

## Gotchas

### Grid column cells with `<Link>` need a router mock

`renderCell` from `~test-utils` renders without a router. Columns whose `cell` uses `<Link>` crash: `Cannot destructure property 'basename' of React.useContext(...) as it is null.`

Opt into the root `react-router-dom` mock's `Link` override:

```text
jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: { children?: ReactNode }) => <>{children}</> };
});
```

The root mock is intentionally NOT global so route-param tests keep the real runtime.

### Overriding the global `@swo/design-system/utils` mock replaces it entirely

The global manual mock spreads `...actual` and overrides `DisplayValue` / `useLocalisation` / `useDesignSystemOptions`. A spec-level `jest.mock("@swo/design-system/utils", () => ({ ... }))` **fully replaces** it — `NO_VALUE` becomes `undefined`, `useLocalisation` disappears.

Two safe patterns:

1. Re-supply every export the code under test touches (simplest for scoped mocks).
2. Extend the global via `requireActual`:
   ```text
   jest.mock("@swo/design-system/utils", () => {
     const actual = jest.requireActual("@swo/design-system/utils");
     return { ...actual, DisplayValue: ({ value }) => <>{value}</> };
   });
   ```

Symptoms of a silent override: highlight-value spans render empty; `NO_VALUE` fallbacks appear as literal `undefined`.

## Testing patterns

### Grid components (thin wrappers)

- Mock `@swo/design-system/grid` (`Grid`, `useGridAsync`, `GridCellSimple`) — use `~test-utils/mocks/designSystemGrid`
- Mock the co-located `*.config` and stub `useGridConfig` return with the props the wrapper spreads (`silentRefresh`, `refresh`, `onEvent`). Typed spies need `as unknown as ReturnType<typeof useGridConfig>` for partial fixtures
- Row-action wiring: capture the `onAction` callback via `mockUseGridConfig.mock.calls[0][1]`, invoke inside `act(...)`, assert modal props changed

### Container components

- Mock the child Details component
- Mock the API hook with `get` returning a resolved value
- Provide `QueryClientProvider` + `MemoryRouter` with route params
- Two tests: happy path + missing-param path

### Grid config hooks (`useColumns`, `useFields`, `useAsyncOptions`, `useGridConfig`)

- Mock every peer hook and rendered leaf component
- Test column order + `fields` mapping (`it.each` is a great fit) and rendered cell output (invoke `column.cell` via `renderCell`)

### Hooks

- `renderHook(() => useHook())` from `@testing-library/react`
- Context-dependent hooks: pass a `wrapper`
- Factory hooks returning functions: capture the returned function, assert output for representative inputs

### Actions

- Mock API hooks, entity hooks, and `useConfirm` from `@swo/design-system/modal`
- `userEvent.click()` for interactions; `await waitFor(...)` for async assertions
- When multiple tests in a file repeat the same `const user = userEvent.setup()` arrange step, extract a tiny local helper or shared test util instead of duplicating the setup ceremony.

### Modals (callback capture)

Mock the shared `Modal` with a capture spy, drive its callbacks:

```text
import { mockSharedModal, mockModal } from "~test-utils/mocks/modal";
import { triggerModalSubmit, triggerModalCancel } from "~test-utils";

jest.mock("~shared/components/modal/Modal", () => mockSharedModal);

// ...
await triggerModalSubmit(mockModal);
triggerModalCancel(mockModal);
```

Rules of thumb:

- Assert only props with behavioural meaning: `isOpen`, `isSubmitting`, `isSubmitDisabled`, the entity payload, wired callbacks
- One test per guard clause (`"does not call remove when no entitlement is provided"`)
- Use `mockModal.mock.lastCall![0]` for "final render" state

### React Query mutation controllers

Need the real query client (`createQueryClientWrapper()`) so `useMutation` state transitions fire. Mock the API method, mock `useErrorDetails.getErrorMessage`, drive via `act(async () => await result.current.remove(entity))`.

Rejection path: `mutateAsync` **re-throws** even though `onError` handles it. Wrap invocation in `await expect(...).rejects.toBeDefined()` (or `.catch(() => undefined)`) or Node prints an unhandled-rejection warning that pollutes the run.

### Wizard steps vs. form controllers — two patterns

- **Wizard steps** read live form state via `useWatch`/`useFormState`/`getValues`. Render inside a real `<FormProvider {...useForm()}>` and inject stub `trigger`/`setValue` when needed.
- **Form controllers** wire `handleSubmit(onSubmit)` into a mutation. Mock the form hook entirely and inject a fake `handleSubmit` that immediately calls the callback with a valid payload — bypasses zod validation so the spec drives the mutation directly.

## When NOT to write a unit test

- **Bootstrap glue** (`entries/StandaloneRoot.tsx`) — requires mocking React DOM. E2e covers it.
- **Barrel files** — TS enforces the surface.
- **Type-only modules** — no runtime behaviour.
- **Path constant literals** (`PARAMS.entitlementId === "entitlementId"`) — assertion repeats the source string. Keep URL _builder_ tests.
- **Exhaustive router smoke coverage** that only proves static React Router wiring — keep tests for meaningful behaviour (`RouteGuard` wiring, default redirects, route-param extraction, component-owned branching), not one assertion per path string.

Rule of thumb: _would a plausible bug in this file survive a passing test?_ If the only failure mode is "the source string changed", it's a change-detector — delete it.

## Scope of a unit test

**Test:** the code's own branching (`null`, role, feature flag); error paths it owns; non-trivial memoization boundaries; callback wiring.

**Don't test:** empty-list rendering when Grid is mocked (mock HTML is identical); translation keys (`useFixedT` is identity-mocked); third-party internals; every forwarded prop; duplicated route-path smoke assertions that only restate static config.

**Null / missing input coverage:** for any input that can be `null`/`undefined` at runtime, add one test with the missing value (nullable relations in column cells, context hooks that can return `undefined`, absent route params).

## AAA pattern

- No `if` statements or branching in tests
- `it.each` / `describe.each` for parameterised tests
- Prefer setup functions / `beforeEach` over inline mocks
- `mockFn.mock.lastCall![0]` for last-invocation assertions

## Test names

Short, specific, behaviour-focused. `describe` for the subject; `it` for the observable behaviour. If the name needs multiple `and`s, split.

Prefer scenario language over raw assertion output or internal implementation details:

- **Avoid assertion-shaped suffixes** like `→ isHidden=%s` / `→ isDisabled=%s`; describe the rule instead (`"sets the actions column visibility for role '%s'"`)
- **Avoid raw URL-heavy titles** when a scenario name is clearer; prefer tab/entity labels over `/organizations/org-1/...` in the description
- **Avoid `noop` jargon**; describe the blocked behaviour (`"does not call X when Y is missing"`)
- **Avoid `passes` / `wires` / `forwards` when a visible effect exists**; prefer the observed result (`"reflects the controller state in the modal"`, `"cancels the modal and updates the selected import date"`)
- **Avoid endpoint-shaped API test titles** like `"issues GET /foo/{id}"`; prefer the business behaviour (`"fetches X by id"`, `"lists X using the provided query"`, `"updates only the organization's name"`)

Common rewrites:

| Anti-pattern                                               | Rewrite                                                       |
| ---------------------------------------------------------- | ------------------------------------------------------------- |
| `"renders the correct X"`                                  | `"renders %s at index=%i"` (parameterised)                    |
| `"notifies parent about X"`                                | `"passes X to useNotifyParentChildModal"`                     |
| `"successfully X"` / `"correctly X"`                       | `"X"` — drop the filler                                       |
| Internal handler in `it()` (`"closeWizard calls onClose"`) | Observable trigger (`"Wizard onClose reports success=false"`) |

Rule of thumb: **subject → verb → observable outcome**.

## Tests to delete on sight

- `"returns a memoized … stable across re-renders"` — tests React internals
- Path literal assertions (`expect(PARAMS.x).toBe("x")`) — change-detectors
- Re-export identity checks — TS's job
- "Not called by default" assertions where the trigger isn't wired in the test — mirrors source shape without proving anything
- Duplicated modal-wiring tests exercising the same code path from two angles
- Inline snapshots for simple structure / attributes when targeted assertions on role, text, classes, props, or SVG attributes would be clearer
- Duplicate router smoke tests where one case already proves the redirect or child-route selection behaviour
- JSDoc above `it("…")` — `it("…")` is the docstring

## Canonical spec file layout

```
1. imports (test-library → aliases → spies from .spec.mocks → source under test)
2. constants / local types
3. inline jest.mock + local mock* spies (only if no .spec.mocks sibling)
4. helper functions
5. describe(...)
```

Extract to `<file>.spec.mocks.ts[x]` when step 3 grows past ~20-30 lines or spans 3+ mocked modules.

## Final pass after finishing test work

Review the whole touched surface (edited specs, sibling `.spec.mocks` files, `src/test-utils/`) for patterns that should be shared instead of copied: render wrappers, typed mock factories, domain factories, callback-invocation helpers, repeated module mock shapes. Extract only patterns appearing in 2+ places or clearly improving readability.

## References

- `./references/testing-conventions.md` — additional testing patterns (containers, grid wrappers, config hooks, actions)
- `./references/troubleshooting.md` — common issues (design-system paths, `@mpt-extension/sdk`, TextEncoder, `transformIgnorePatterns`, `column.cell` calling)
