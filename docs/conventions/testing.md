# Frontend testing conventions

Unit tests for `frontend/src/**` using
[`jest@30`](https://jestjs.io/) +
[`@swc/jest`](https://swc.rs/docs/usage/jest) (CJS transform) +
[`jest-environment-jsdom`](https://github.com/jsdom/jsdom) +
[`@testing-library/react@16`](https://testing-library.com/docs/react-testing-library/intro).
Config in [`frontend/jest.config.js`](../../frontend/jest.config.js); global
setup in [`frontend/jest.setup.js`](../../frontend/jest.setup.js).

`npm test` runs jest + `tsc` + prettier + eslint in parallel via
`npm-run-all --parallel --continue-on-error`. SWC skips type-checking during
jest — **typed-spy drift only surfaces at the `tsc` step**, so don't trust a
green jest run alone.

## File naming

- **`.spec.tsx`** for specs that render JSX; **`.spec.ts`** for utilities and
  pure-logic hooks. Never `.test.*`.
- **`.spec.mocks.tsx`** (or `.ts`) — sibling file holding the `jest.mock(...)`
  prelude when it grows past ~20-30 lines or 3+ mocked modules.
  [`frontend/.prettierrc.json`](../../frontend/.prettierrc.json) has a
  dedicated import-order group that sorts `.spec.mocks` imports **before** the
  source-under-test. Don't reorder — if the source import lands first, real
  modules resolve before mocks apply.
- Base name mirrors the source: `UsersGrid.tsx` → `UsersGrid.spec.tsx`
  (+ optional `UsersGrid.spec.mocks.tsx`).

## Coverage floor

Keep unit-test coverage **above 85%**. Treat `<85%` as a failed outcome even
if jest itself passes. Add behaviour-finding tests or delete shallow
change-detectors before merging. Run coverage when touching branching logic,
route composition, or shared test infrastructure.

## Mocking rules

### Mock the exact design-system subpath

Source imports from `@swo/design-system/<component>` (see
[Design system import discipline](#design-system-import-discipline) below).
Mock the **exact same path**:

```ts
jest.mock("@swo/design-system/grid", () => ({
  Grid: () => null,
  useGridAsync: jest.fn(),
  GridCellSimple: ({ children }: { children?: unknown }) => children,
}));
```

The shortened `@swo/<component>` form from `mpt-vikings-ui` does **not** match
anything in this repo — the mock silently no-ops and the real module runs.

### Never spread the real design-system module

```ts
// ❌ blows the 512 MB jest worker heap
jest.mock("@swo/design-system/grid", () => ({
  ...jest.requireActual("@swo/design-system/grid"),
  Grid: () => null,
}));
```

Design-system subpaths pull enormous dependency graphs. Enumerate the exports
you need instead.

### Pre-mocked modules (do not re-mock)

Globally activated in [`frontend/jest.setup.js`](../../frontend/jest.setup.js):

- `@swo/design-system/utils` — root manual mock passes `...actual` through and
  overrides `useDesignSystemOptions`, `useLocalisation`, `DisplayValue`.
- `@mpt-extension/sdk` — `{ setup, http }` stubs (the package is ESM-only and
  cannot be resolved in the CJS jest runtime).
- `~shared/hooks/useFixedT` — identity function; `t("key")` returns `"key"`.

Also globally stubbed: `TextEncoder` / `TextDecoder` (needed at
`react-router-dom` import time) and `ResizeObserver` (design-system expects
it).

**Root manual mocks that are NOT global** (opt in per spec):

- [`__mocks__/react-router-dom.tsx`](../../frontend/src/__mocks__/react-router-dom.tsx)
  — pass-through, overrides `Link`. Route-param tests keep the real runtime by default.
- [`__mocks__/react-i18next.tsx`](../../frontend/src/__mocks__/react-i18next.tsx)
  — identity `useTranslation`; `Trans` renders `i18nKey`.

### Never mock

- `react`, `react-dom`, `react-dom/client` — bootstrap files (`createRoot`)
  are covered by e2e, not units.
- Full `react-router-dom` in a spec-specific factory. Use `MemoryRouter` +
  `Routes` + `Route` for `useParams` tests.

### Overriding the global `@swo/design-system/utils` replaces it entirely

A spec-level `jest.mock("@swo/design-system/utils", () => ({ ... }))` **fully
replaces** the global manual mock — `NO_VALUE` becomes `undefined`,
`useLocalisation` disappears. Two safe patterns:

1. Re-supply every export the code under test touches, or
2. Extend the global via `requireActual`:
   ```ts
   jest.mock("@swo/design-system/utils", () => {
     const actual = jest.requireActual("@swo/design-system/utils");
     return { ...actual, DisplayValue: ({ value }) => <>{value}</> };
   });
   ```

Symptoms of a silent override: highlight-value spans render empty; `NO_VALUE`
fallbacks appear as literal `undefined`.

## Type spies from the source signature

Untyped `jest.fn()` returns `jest.Mock<any, any>` — `mockReturnValue(...)` and
`.mock.lastCall[0]` accept anything and drift silently. Type every spy against
the real signature so `tsc` catches drift:

| Spy target                                 | Typing                                                           |
| ------------------------------------------ | ---------------------------------------------------------------- |
| Hook                                       | `jest.MockedFunction<typeof realHook>`                           |
| Method on a hook's returned object         | `jest.MockedFunction<ReturnType<typeof useApi>["method"]>`       |
| Function returned FROM a hook              | `jest.MockedFunction<ReturnType<typeof useHook>>`                |
| Component prop-capture spy                 | `jest.MockedFunction<(props: ComponentProps<typeof C>) => void>` |
| Generic hook (e.g. `useReactQueryRqlGrid`) | leave untyped — `MockedFunction` collapses generics to defaults  |

When wrapping a spy with a spreader, use `Parameters<typeof realFn>` (not
`...args: unknown[]`) so the call site drifts too:

```ts
jest.mock("../hooks/useForceImportController", () => ({
  useForceImportController: (...args: Parameters<typeof useForceImportController>) =>
    mockUseForceImportController(...args),
}));
```

**Prefer source-exported prop types** over handwritten shapes: `ComponentProps<typeof X>`,
`Pick<ComponentProps<typeof X>, "a" | "b">`, `ReturnType<typeof useHook>`.
Reserve handwritten types for true test-harness state the app doesn't export.

**Partial fixtures a typed spy rejects**: prefer supplying the missing fields
with realistic defaults; otherwise cast tight at the call site —
`mockReturnValue({ currency: "USD" } as OrganizationRead)`, never `as any` the
spy itself.

## Shared test infrastructure

[`frontend/src/test-utils/`](../../frontend/src/test-utils/) (exported via
`~test-utils`). Use these before hand-rolling.

### Render wrappers

- `renderWithRouter(ui, { initialUrl, routePath })` — for `useParams` tests.
- `renderWithEntitlementRoute(ui, { id, routePath })` /
  `renderWithOrganizationRoute(ui, { id, routePath })` — entity-detail shells.
- `createQueryClientWrapper()` — real `QueryClientProvider` with
  `{ queries: { retry: false } }` for `useMutation` state tests.

### Grid helpers

- `renderCell(column, item)` — invoke a grid column's `cell` function safely
  (typed as `Pick<GridColumnDefinition<T>, "cell" | "name">`).
- `columnByName(columns, name)` — column lookup.

### Modal helpers

- `triggerModalSubmit(mockModal)` / `triggerModalCancel(mockModal)` — invoke
  captured `<Modal>` callbacks inside `act(...)`.

### Factories

[`frontend/src/test-utils/factories/`](../../frontend/src/test-utils/factories/)
holds typed `Partial<T>`-overlay builders: `makeAccount`, `makeDatasource`,
`makeEmployee`, `makeEntitlement`, `makeOrganization`. Prefer these over
hand-constructed fixtures.

### Shared mock modules

[`frontend/src/test-utils/mocks/`](../../frontend/src/test-utils/mocks/) holds
pre-built `jest.mock` targets with their spies co-exported:

```ts
import { mockDesignSystemGrid, mockGridProps, mockUseGridAsync } from "~test-utils/mocks/designSystemGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
```

Each file exports both the **spy** (`mockUseX`) and the **module shape**
(`mockXModule`), wired to call the spy. Both names must start with `mock*` so
jest's hoist rule accepts them.

**Promote to a shared mock when 2+ specs mock the same module with an
equivalent factory.** Rules:

- One mock per file. Don't bundle unrelated mocks together.
- No `index.ts` barrels in `mocks/`. Callers import specific paths so the
  reader sees exactly which module gets mocked.
- Names describe what's mocked (`gridHooks`, not `sharedGridHooks` — everything
  here is shared by definition).

Current inventory: browse
[`src/test-utils/mocks/`](../../frontend/src/test-utils/mocks/).

## Design system import discipline

Mirrors the rest of the codebase — see
[Naming conventions](./naming.md). Always import by subpath
(`@swo/design-system/button`), never from the root barrel. Reasons:

1. **Bundle size**: subpath imports cost 100s of KB each; the root barrel pulls everything.
2. **Mock resolution**: a `jest.mock(…)` only matches the exact path the
   source imports — a root-barrel source + subpath mock (or vice-versa)
   silently no-ops.

## Spec-scoped ESLint rules

[`frontend/eslint.config.mjs`](../../frontend/eslint.config.mjs) enables
`eslint-plugin-jest` / `-testing-library` / `-jest-dom` on spec globs. Two
consequences worth internalising:

- Use `screen.getBy*` — do **not** destructure from `render()`.
- Use `toHaveTextContent(...)` — not `expect(el.textContent).toBe(...)`.

## When NOT to write a unit test

- **Bootstrap glue** (`entries/StandaloneRoot.tsx`) — mocking React DOM is
  more work than value. E2e covers it.
- **Barrel files** — TS enforces the surface.
- **Type-only modules** — no runtime behaviour.
- **Path constant literals** (`PARAMS.entitlementId === "entitlementId"`) —
  assertion repeats the source string. Keep URL _builder_ tests.
- **Exhaustive router smoke coverage** that only restates static React Router
  wiring — keep tests for `RouteGuard` wiring, default redirects, route-param
  extraction, and component-owned branching.

Rule of thumb: _would a plausible bug in this file survive a passing test?_
If the only failure mode is "the source string changed", it's a
change-detector — delete it.

## Scope of a unit test

**Test:** the code's own branching (`null`, role, feature flag); error paths
it owns; non-trivial memoization boundaries; callback wiring.

**Don't test:** empty-list rendering when the Grid is mocked (mock HTML is
identical); translation keys (`useFixedT` is identity-mocked); third-party
internals; every forwarded prop; duplicated route-path smoke assertions.

**Null / missing input coverage**: for any input that can be `null` /
`undefined` at runtime (nullable relations in column cells, context hooks that
can return `undefined`, absent route params), add one test with the missing
value.

## Test name style

Short, specific, behaviour-focused. `describe` for the subject; `it` for the
observable behaviour. If the name needs multiple `and`s, split.

- **Avoid assertion-shaped suffixes** like `→ isHidden=%s` / `→ isDisabled=%s`;
  describe the rule (`"sets the actions column visibility for role '%s'"`).
- **Avoid URL-heavy titles** when a scenario name is clearer — prefer tab or
  entity labels over `/organizations/org-1/...`.
- **Avoid `noop`** jargon — describe the blocked behaviour
  (`"does not call X when Y is missing"`).
- **Avoid `passes` / `wires` / `forwards` when a visible effect exists** —
  prefer the observed result
  (`"reflects the controller state in the modal"`,
  `"cancels the modal and updates the selected import date"`).
- **Avoid endpoint-shaped API titles** like `"issues GET /foo/{id}"` — prefer
  the business behaviour (`"fetches X by id"`, `"lists X using the provided query"`).

Rule of thumb: **subject → verb → observable outcome.**

## Patterns to delete on sight

- `"returns a memoized … stable across re-renders"` — tests React internals.
- Path-literal assertions (`expect(PARAMS.x).toBe("x")`) — change-detectors.
- Re-export identity checks — TS's job.
- "Not called by default" assertions where the trigger isn't wired in the
  test — mirrors source shape without proving anything.
- Duplicated modal-wiring tests exercising the same path from two angles.
- Inline snapshots for simple structure / attributes when targeted role, text,
  class, prop, or SVG-attribute assertions would be clearer.
- Duplicate router smoke tests where one case already proves the redirect or
  child-route selection.
- JSDoc above `it("…")` — the `it("…")` string is the docstring.

## See also

- [API hook conventions](./api-hooks.md) — the hook shapes test specs assume.
- [Naming conventions](./naming.md) — file & folder casing.
- [i18n conventions](./i18n.md) — why `useFixedT` is identity-mocked in tests.
- [Modals](./modals.md) — the `useModalToggle` + controller shape the modal
  specs assert against.
- [`.claude/skills/mpt-module-testing/SKILL.md`](../../.claude/skills/mpt-module-testing/SKILL.md)
  — Claude Code skill that layers canonical patterns on top of these rules
  (Grid wrapper / Container / hook / modal callback / wizard-step recipes,
  spec-file layout, mutation-controller gotchas). **This doc wins on drift.**
