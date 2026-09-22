# Troubleshooting

Common issues when writing unit tests in `ffc-extension/frontend/` and how to fix them.

---

## ffc-extension specifics (READ FIRST)

Pitfalls unique to this repo's Jest setup (CJS + `@swc/jest` + jsdom).

### Problem: `Cannot find module '@mpt-extension/sdk' from ...`

**Cause:** `@mpt-extension/sdk`'s `package.json` declares only `"exports": { ".": { "import": "./dist/index.js" } }`. In Jest's CJS mode `require()` refuses to resolve packages that expose only the `import` condition.

**Solution:** use the root manual mock at `frontend/__mocks__/@mpt-extension/sdk.ts`. Do **not** assume it is globally enabled from `frontend/jest.setup.js` unless setup explicitly opts it in.

```text
// opt in when a spec really needs it
jest.mock("@mpt-extension/sdk");
```

If you see the error, verify the root manual mock file still exists and that your test setup/spec opts in correctly when needed.

### Problem: `ReferenceError: TextEncoder is not defined` when importing `react-router-dom`

**Cause:** jsdom does not provide `TextEncoder` / `TextDecoder` globally. `react-router-dom` (v6+) touches `TextEncoder` at import time, so any spec that renders under `MemoryRouter` — or that transitively triggers `jest.requireActual('react-router-dom')` from `jest.setup.js` — crashes on module load.

**Solution:** already stubbed globally in `frontend/jest.setup.js`:

```text
import {TextEncoder, TextDecoder} from 'node:util';
Object.assign(globalThis, {TextEncoder, TextDecoder});
```

### Problem: `Jest encountered an unexpected token ... export {}` from a `node_modules` package

**Symptom:** Jest tries to run an ESM-only file from `@swo/…`, `@tanstack/…`, `axios`, `zod`, `@mpt-extension/…`, etc. and dies on `export`/`import` syntax.

**Cause:** by default Jest ignores `node_modules` when transforming. If a dependency ships ESM without a CJS fallback, that raw ESM leaks into the test runtime.

**Solution:** the config already includes those packages in `transformIgnorePatterns` so SWC transpiles them to CJS:

```text
// jest.config.js
transformIgnorePatterns: [
  '/node_modules/(?!(@swo|@mpt-extension|axios|@tanstack|react-i18next|zod|zod-i18n-map|@hey-api|@hookform)/)',
],
```

If a new ESM-only dependency fails the same way, extend the negative lookahead.

### Problem: React state doesn't update when you call a captured callback directly

**Symptom:** you grab `onAction` (or another callback) from `mockUseGridConfig.mock.calls[0][1]` and call it. The parent component's `useState` fires, but the child mock never re-renders with the new props. Assertions on the "after" state fail.

**Cause:** state updates outside `act()` are dropped by React 18/19 in tests.

**Solution:** wrap the invocation in `act(...)`:

```text
import { act } from "@testing-library/react";

const onAction = mockUseGridConfig.mock.calls[0][1];
act(() => onAction("force_import", item));

expect(mockForceImportModal.mock.calls[mockForceImportModal.mock.calls.length - 1][0])
  .toMatchObject({ isOpen: true });
```

### Problem: `TS2339: Property 'toBeInTheDocument' does not exist on type 'JestMatchers<HTMLElement>'`

**Cause:** `tsconfig.json` `types` list doesn't include `@testing-library/jest-dom`. Runtime works (setup file registers the matchers) but the TS compiler doesn't know about them.

**Solution:** add to `frontend/tsconfig.json`:

```text
{
  "compilerOptions": {
    "types": ["node", "jest", "@testing-library/jest-dom"]
  }
}
```

### Problem: `TS2349: This expression is not callable` on `column.cell!(item)`

**Cause:** `GridColumnDefinition.cell` is typed as `ReactNode | ((item: T) => ReactNode)`. The non-null assertion `!` only strips `undefined`, not the `ReactNode` branch of the union, so TS still refuses to call it.

**Solution:** cast to the function shape:

```text
const { getByTestId } = render(
  renderCell(column as Pick<GridColumnDefinition<DatasourceRead>, "cell" | "name">, item),
);
```

## Design System Mocking Issues

### Problem: Mock not applied to a design-system component

**Symptom:** the real component renders and you can't find the mock's `data-testid`.

**Cause:** the mock path doesn't match the source import. In `ffc-extension/frontend` source imports from `@swo/design-system/[component]` (full path), NOT `@swo/[component]`. Jest treats them as distinct module IDs, so a mock on the shorter path never intercepts.

```text
// ❌ Wrong (pattern from mpt-vikings-ui, wrong for this repo)
jest.mock("@swo/grid", () => ({ Grid: () => null }));

// ✅ Correct — matches actual source imports
jest.mock("@swo/design-system/grid", () => ({ Grid: () => null }));
```

Applies to every design-system subpath: `@swo/design-system/grid`, `@swo/design-system/entity-reference-cell`, `@swo/design-system/modal`, `@swo/design-system/dropdown`, etc.

### Problem: Heap OOM when spreading the real design-system module

**Symptom:** `FATAL ERROR: Reached heap limit Allocation failed` when a spec starts. Stack trace points at a factory calling `jest.requireActual("@swo/design-system/…")`.

**Cause:** `@swo/design-system/grid` and siblings are huge modules with heavy side effects. Spreading the real module inside a mock factory pulls the entire dependency graph into the test process.

```text
// ❌ Wrong
jest.mock("@swo/design-system/grid", () => ({
  ...jest.requireActual("@swo/design-system/grid"),
  buildRqlQuery: jest.fn(),
}));

// ✅ Return only the runtime exports the code under test uses; type-only exports are erased by SWC
jest.mock("@swo/design-system/grid", () => ({
  buildRqlQuery: jest.fn(),
}));
```

### Problem: Pre-mocked module being mocked again

**Symptom:** `Warning: Duplicate mock for '...'`.

**Cause:** module already mocked in `jest.setup.js`, or it is a root manual mock you are treating as globally enabled when it is not.

**Solution:** remove the mock from your spec. Pre-mocked modules:

- `@swo/design-system/utils` (`useDesignSystemOptions`, `useLocalisation`, `DisplayValue`) — globally enabled
- `~shared/hooks/useFixedT` (returns identity function)

Root manual mocks / special cases available, but **not assumed globally active**:

- `react-router-dom` (pass-through mock overriding `Link`)
- `react-i18next` (`useTranslation` returns identity `t`; `Trans` renders `i18nKey`)
- `@mpt-extension/sdk` (`{ setup, http }`; ESM-only package)

Global stubs: `TextEncoder` / `TextDecoder` on `globalThis`.

---

## Render / Query Issues

### Problem: `No QueryClient set, use QueryClientProvider to set one`

**Cause:** the code under test (or one of its hooks) calls `useQueryClient` / `useQuery`, but the test doesn't wrap it in a `QueryClientProvider`.

```text
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return createQueryClientWrapper();
}

const { result } = renderHook(() => useSomething(), { wrapper: createWrapper() });
```

If you're testing a shallow wrapper you can mock the config hook that pulls in React Query instead — see the canonical `DataSourcesGrid.spec.tsx` (`mockUseGridConfig.mockReturnValue({...})`).

### Problem: Async assertion never fires

**Symptom:** `expect(...).toBeInTheDocument()` fails on data that renders after a fetch.

**Solution:** `await waitFor(...)`:

```text
await waitFor(() => {
  expect(screen.getByTestId("data")).toBeInTheDocument();
});
```

For user events use `userEvent` (already awaits its own effects):

```text
const user = userEvent.setup();
await user.click(screen.getByRole("button", { name: /save/i }));
```

---

## Path Alias Issues

### Problem: `Cannot find module '~shared/…'` in tests

**Cause:** `moduleNameMapper` in `jest.config.js` is missing the alias, or the file doesn't exist at the mapped path.

**Solution:** `frontend/jest.config.js` maps:

```
~api/*            → src/api/*
~app/*            → src/app/*
~features/*       → src/features/*
~organizations/*  → src/features/organizations/*
~entitlements/*   → src/features/entitlements/*
~shared/*         → src/shared/*
~i18n/*           → src/i18n/*
```

If you add a new top-level alias in `tsconfig.json`, add the matching entry to `jest.config.js` (`moduleNameMapper`) — TS and Jest maintain separate maps.

**Known drift:** `tsconfig.json` declares `~fixes/*` → `fixes/*`, but `jest.config.js` does not map it. No spec currently imports from `~fixes`, but the first one to do so will need to add the mapping to `moduleNameMapper`.

---

## Prevention Checklist

Before committing a spec:

- [ ] `.spec.tsx` extension
- [ ] Mocks use classic `jest.mock` + static `import` (SWC hoists in CJS mode)
- [ ] Design-system mocks use the full `@swo/design-system/[component]` path
- [ ] No re-mocking of globally enabled modules (`useFixedT`, `@swo/design-system/utils`)
- [ ] Root manual mocks (`react-router-dom`, `react-i18next`, `@mpt-extension/sdk`) are treated as opt-in unless setup explicitly enables them
- [ ] Mock factory returns only runtime exports the code under test uses (no `...jest.requireActual(...)` for big design-system modules)
- [ ] Shared mocks / shared test utils prefer source-exported types or `ComponentProps<typeof ...>` over handwritten prop shapes
- [ ] State-changing callbacks invoked from test code wrapped in `act(...)`
- [ ] Path aliases (`~shared/`, `~organizations/`, etc.) used consistently
- [ ] `npm test` passes locally
- [ ] `npm run typecheck` passes

---

**See also:** [testing-conventions.md](./testing-conventions.md) · [test-quick-reference.md](./test-quick-reference.md)
