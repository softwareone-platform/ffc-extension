# Testing Conventions

Test structure, placement, mocking rules, and testing patterns for modules in `ffc-extension/frontend/`.

Stack: `jest@30` + `@swc/jest` (CJS transform) + `jest-environment-jsdom` + `@testing-library/react@16`.

Classic `jest.mock(path, factory)` works — SWC hoists it above `import`. Design-system mocks must use the full `@swo/design-system/[component]` path (see [Mocking Rules](#mocking-rules) below).

---

## Test File Basics

### Extension

Always `.spec.tsx` (or `.spec.ts` for utilities without JSX). Never `.test.tsx`.

### Co-location

Tests live next to source files:

```
data-sources/
├── DataSources.tsx
├── DataSources.spec.tsx
├── DataSourcesGrid.tsx
├── DataSourcesGrid.spec.tsx
├── DataSourcesGrid.config.tsx
├── DataSourcesGrid.config.spec.tsx
└── hooks/
    ├── useActionOptions.tsx
    └── useActionOptions.spec.tsx
```

---

## Mocking Rules

### Design System Components

Canonical rules and snippets: [SKILL.md → Design System Mocking](../SKILL.md#design-system-mocking--use-the-real-import-path).

Two things that bite repeatedly:

- Use the FULL `@swo/design-system/[component]` path (not the shortened `@swo/[component]` from `mpt-vikings-ui`) — otherwise Jest treats them as distinct module IDs and the mock silently no-ops.
- Return only the runtime exports the code under test actually uses. Type-only exports (`GridColumnDefinition`, `UseAsyncGridConfig`, etc.) are erased by SWC. Do **not** `...jest.requireActual("@swo/design-system/...")` inside a factory — the real module is huge and blows the heap (see [troubleshooting.md](./troubleshooting.md#problem-heap-oom-when-spreading-the-real-design-system-module)).

### Pre-Mocked Modules

Full canonical list: [SKILL.md → Pre-Mocked Modules](../SKILL.md#pre-mocked-modules-already-in-jestsetupjs--do-not-mock-again).

Summary: `~shared/hooks/useFixedT`, `react-i18next`, `react-router-dom` (Link only), `@swo/design-system/utils`, `@mpt-extension/sdk` are stubbed globally. Global stubs: `TextEncoder` / `TextDecoder`. Don't re-mock these in specs.

### Never Mock

- `react`
- `react-dom`
- The full `react-router-dom` (mock specific hooks if truly necessary, but prefer `MemoryRouter`)

---

## Test Wrappers

Basic `MemoryRouter` and `QueryClientProvider` snippets live in [SKILL.md → Test Wrappers](../SKILL.md#test-wrappers). What's project-specific:

**`renderHook` with React Query** (used for hooks that call `useQuery` / `useQueryClient`):

```typescript
function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: PropsWithChildren) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const { result } = renderHook(() => useMyHook(), { wrapper: createWrapper() });
```

Canonical example: `frontend/src/shared/hooks/useReactQueryRqlGrid.spec.tsx`.

---

## Testing Patterns

### Container components (`FooContainer`)

- Mock the child component (`Foo`) so the container's logic is tested in isolation
- Wrap in `MemoryRouter` if the container reads route params
- Two tests: happy path (all params present) + missing-param path

### Thin Grid wrappers (`FooGrid`)

- Mock `@swo/design-system/grid` (`Grid`, `useGridAsync`, `GridCellSimple`)
- Mock the co-located `Foo.config` module — stub `useGridConfig` to return `{ silentRefresh, refresh, onEvent, columns, fields }`
- If the wrapper wires row actions (e.g. force-import modal), capture `onAction` via `mockUseGridConfig.mock.calls[0][1]`, invoke inside `act(() => ...)`, then assert modal props

### Grid config hooks (`useColumns`, `useFields`, `useAsyncOptions`, `useGridConfig`)

- Mock every peer hook (`~organizations/api`, `~organizations/providers/...`, `~shared/hooks/useReactQueryRqlGrid`, `~shared/hooks/useUserRole`, `~shared/hooks/useGridInfoDialogConfiguration`, and any local `./hooks/*`)
- Mock all rendered leaf components (`@swo/design-system/entity-reference-cell`, `~shared/components/grid/GridCellCurrency`, `~shared/components/grid/GridCellDate`, `~shared/components/grid/GridCellDynamicActions`, `~shared/components/custom-icons/CustomIcon`)
- Test structure (column order, `fields` mapping — good `it.each` case) + rendered cell output (call `column.cell!(item)` after casting to a function; see canonical spec)

### Hooks

- `renderHook(() => useHook())` from `@testing-library/react`
- For context-dependent hooks (`useOrganizationContext`, React Query hooks), pass a `wrapper`
- For factory hooks that return functions (`useActionOptions`, `useAsyncOptions`), capture the returned function and assert its output for representative inputs

### Actions

- Mock API hooks and entity hooks at the module level
- Mock `useConfirm` from `@swo/design-system/modal`
- Use `userEvent.click()` for interactions
- `await waitFor(...)` for async assertions

---

## AAA Pattern

Follow **Arrange-Act-Assert** strictly:

- No `if` statements or branching in tests
- Use `it.each` / `describe.each` for parameterized tests (column ↔ fields mapping is a great case — see canonical spec)
- Prefer setup functions / `beforeEach` over inline mocks

---

## Canonical Examples

Copy from these — they are the reference specs for this repo:

- **Container:** `frontend/src/features/organizations/details/data-sources/DataSources.spec.tsx`
- **Grid wrapper (with `act()`):** `frontend/src/features/organizations/details/data-sources/DataSourcesGrid.spec.tsx`
- **Config hooks (largest, most patterns):** `frontend/src/features/organizations/details/data-sources/DataSourcesGrid.config.spec.tsx`
- **Hook with React Query wrapper:** `frontend/src/shared/hooks/useReactQueryRqlGrid.spec.tsx`

---

## Coverage Guidance

**Do test:**

- Component renders without errors
- Correct props passed to children (mocked)
- User interactions trigger expected behavior
- Conditional rendering based on state/props/role
- Hook return values and their structure
- Row-action wiring (capture callback, invoke, assert side-effect)

**Don't test:**

- Implementation details (private helpers)
- Third-party library internals (e.g. React Query cache internals)
- Trivial code (getters/setters, straight-through re-exports)
- CSS/styling (unless it's functional)

---

**See also:** [test-quick-reference.md](./test-quick-reference.md) · [troubleshooting.md](./troubleshooting.md)
