# Troubleshooting

Common issues when writing unit tests in `ffc-extension/frontend/` and how to fix them.

---

## ffc-extension specifics (READ FIRST)

### `Cannot find module '@mpt-extension/sdk' from ...`

**Cause:** `@mpt-extension/sdk`'s `package.json` declares only `"exports": { ".": { "import": "./dist/index.js" } }`. Jest's CJS mode can't resolve `import`-only packages.

**Solution:** the SDK is already mocked globally via `frontend/jest.setup.js` (`jest.mock('@mpt-extension/sdk', …, { virtual: true })`) using the root manual mock at `frontend/__mocks__/@mpt-extension/sdk.ts`. If you see the error, verify `jest.setup.js` still registers it and the manual mock file exists.

### `ReferenceError: TextEncoder is not defined` when importing `react-router-dom`

**Cause:** jsdom doesn't provide `TextEncoder`/`TextDecoder`. `react-router-dom` (v6+) touches `TextEncoder` at import time.

**Solution:** already stubbed globally in `frontend/jest.setup.js`. If a new spec still hits this, check the setup file was loaded (`setupFilesAfterEach` in `jest.config.js`).

### `Jest encountered an unexpected token ... export {}` from a `node_modules` package

**Cause:** Jest ignores `node_modules` when transforming by default. If a dep ships ESM without a CJS fallback, raw ESM leaks into the runtime.

**Solution:** `jest.config.js` includes the ESM-only deps in `transformIgnorePatterns` (negative lookahead) so SWC transpiles them. If a new ESM-only dep fails the same way, extend the lookahead.

### React state doesn't update when you call a captured callback directly

**Symptom:** you grab `onAction` from `mockUseGridConfig.mock.calls[0][1]` and call it. The `useState` fires, but the child mock never re-renders with new props.

**Cause:** state updates outside `act()` are dropped by React 18/19 in tests.

**Solution:** wrap the invocation:

```text
import { act } from "@testing-library/react";

const onAction = mockUseGridConfig.mock.calls[0][1];
act(() => onAction("force_import", item));

expect(mockForceImportModal.mock.lastCall![0]).toMatchObject({ isOpen: true });
```

### `TS2339: Property 'toBeInTheDocument' does not exist on JestMatchers`

**Cause:** `tsconfig.json` `types` list doesn't include `@testing-library/jest-dom`. Runtime works, TS doesn't.

**Solution:** add to `frontend/tsconfig.json`:

```text
"types": ["node", "jest", "@testing-library/jest-dom"]
```

### `TS2349: This expression is not callable` on `column.cell!(item)`

**Cause:** `GridColumnDefinition.cell` is typed as `ReactNode | ((item: T) => ReactNode)`. `!` only strips `undefined`, not the `ReactNode` branch.

**Solution:** use `renderCell` from `~test-utils` — it casts to the function shape:

```text
const { getByTestId } = render(renderCell(column, item));
```

---

## Design system mocking issues

### Mock not applied to a design-system component

**Symptom:** the real component renders; the mock's `data-testid` is missing.

**Cause:** the mock path doesn't match the source import. `ffc-extension/frontend` imports from `@swo/design-system/[component]` (full path), not `@swo/[component]`. Jest treats them as distinct module IDs.

```text
// ❌ Wrong (mpt-vikings-ui pattern)
jest.mock("@swo/grid", () => ({ Grid: () => null }));

// ✅ Correct
jest.mock("@swo/design-system/grid", () => ({ Grid: () => null }));
```

Applies to every subpath: `/grid`, `/entity-reference-cell`, `/modal`, `/dropdown`, etc.

### Heap OOM when spreading the real design-system module

**Symptom:** `FATAL ERROR: Reached heap limit Allocation failed`. Stack points at `jest.requireActual("@swo/design-system/…")`.

**Cause:** design-system subpaths are huge modules with heavy side effects. Spreading them pulls the entire dependency graph in. `workerIdleMemoryLimit: '512MB'` will trip.

```text
// ❌
jest.mock("@swo/design-system/grid", () => ({
  ...jest.requireActual("@swo/design-system/grid"),
  buildRqlQuery: jest.fn(),
}));

// ✅ enumerate only the runtime exports the code under test uses
jest.mock("@swo/design-system/grid", () => ({
  buildRqlQuery: jest.fn(),
}));
```

### `Warning: Duplicate mock for '...'`

**Cause:** module already mocked in `jest.setup.js`. See SKILL.md → Pre-mocked modules for the current list.

**Solution:** remove the spec-level `jest.mock(...)`. To extend the global (e.g. add another `@swo/design-system/utils` export), use `requireActual` and spread — see SKILL.md → "Overriding the global `@swo/design-system/utils` mock replaces it entirely".

---

## Render / query issues

### `No QueryClient set, use QueryClientProvider to set one`

**Cause:** the code under test calls `useQueryClient` / `useQuery` without a provider.

**Solution:** wrap with `createQueryClientWrapper()` from `~test-utils`:

```text
const { result } = renderHook(() => useSomething(), { wrapper: createQueryClientWrapper() });
```

For shallow wrappers, mock the config hook that pulls in React Query instead (see `DataSourcesGrid.spec.tsx`).

### Async assertion never fires

**Solution:** `await waitFor(...)` for data that renders after a fetch. `userEvent` already awaits its own effects, so don't wrap `user.click(...)` in `waitFor`.

```text
await waitFor(() => expect(screen.getByTestId("data")).toBeInTheDocument());

const user = userEvent.setup();
await user.click(screen.getByRole("button", { name: /save/i }));
```

---

## Path alias issues

### `Cannot find module '~shared/…'` in tests

**Cause:** `jest.config.js` `moduleNameMapper` is missing the alias. `tsconfig.json` `paths` and `moduleNameMapper` are separate resolvers.

**Solution:** add the mapping to both. Existing aliases live in `frontend/jest.config.js`.

**Known drift:** `tsconfig.json` declares `~fixes/*` → `fixes/*` but `jest.config.js` doesn't map it. First spec to import from `~fixes` must add the mapping.

---

## Prevention checklist

Before committing a spec:

- [ ] `.spec.tsx` extension
- [ ] Design-system mocks use the full `@swo/design-system/[component]` path
- [ ] No re-mocking pre-mocked modules (see SKILL.md → Pre-mocked modules)
- [ ] Mock factories enumerate runtime exports — no `...jest.requireActual(...)` for design-system subpaths
- [ ] Shared mocks / utils use source-exported types (`import type`, `Pick`, `ComponentProps<typeof …>`)
- [ ] State-changing callbacks invoked from test code wrapped in `act(...)`
- [ ] Path aliases used consistently
- [ ] `npm test` passes locally (jest + tsc + prettier + eslint all green)

---

**See also:** [SKILL.md](../SKILL.md) · [testing-conventions.md](./testing-conventions.md)
