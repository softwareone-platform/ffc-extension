# Testing Conventions — Extended Patterns

Supplements SKILL.md with fuller pattern breakdowns. Read SKILL.md first for critical rules, mocking, and shared infrastructure.

## Testing patterns (expanded)

### Container components (`FooContainer`)
- Mock the child component so the container's logic is tested in isolation
- Wrap in `MemoryRouter` if the container reads route params
- Two tests minimum: happy path (all params present) + missing-param path

### Thin Grid wrappers (`FooGrid`)
- Mock `@swo/design-system/grid` via `~test-utils/mocks/designSystemGrid`
- Mock the co-located `Foo.config` — stub `useGridConfig` to return `{ silentRefresh, refresh, onEvent, columns, fields }`
- If the wrapper wires row actions, capture `onAction` via `mockUseGridConfig.mock.calls[0][1]`, invoke inside `act(() => ...)`, assert modal props

### Grid config hooks (`useColumns`, `useFields`, `useAsyncOptions`, `useGridConfig`)
- Mock every peer hook (`~organizations/api`, `~organizations/providers/…`, `~shared/hooks/useReactQueryRqlGrid`, `~shared/hooks/useUserRole`, `~shared/hooks/useGridInfoDialogConfiguration`, local `./hooks/*`)
- Mock all rendered leaf components (`@swo/design-system/entity-reference-cell`, `~shared/components/grid/GridCellCurrency`, `~shared/components/grid/GridCellDate`, `~shared/components/grid/GridCellDynamicActions`, `~shared/components/custom-icons/CustomIcon`)
- Test structure (column order, `fields` mapping — good `it.each` case) + rendered cell output via `renderCell(column, item)`

### Hooks
- `renderHook(() => useHook())` from `@testing-library/react`
- Context-dependent hooks: pass a `wrapper`
- Factory hooks returning functions: capture the returned function and assert output for representative inputs

### Actions
- Mock API hooks and entity hooks at module level
- Mock `useConfirm` from `@swo/design-system/modal`
- `userEvent.click()` for interactions; `await waitFor(...)` for async assertions

## Coverage guidance

**Do test:**
- Component renders without errors
- Correct props passed to mocked children
- User interactions trigger expected behaviour
- Conditional rendering based on state/props/role
- Hook return values and their structure
- Row-action wiring (capture callback → invoke → assert side-effect)

**Don't test:**
- Implementation details (private helpers)
- Third-party library internals (React Query cache, RQL parser)
- Trivial code (getters/setters, re-exports)
- CSS/styling unless functional

## Canonical reference specs

`frontend/src/features/organizations/details/data-sources/`
- `DataSources.spec.tsx` — container + `MemoryRouter` + child mock
- `DataSourcesGrid.spec.tsx` + `.spec.mocks.tsx` — thin Grid wrapper, captured `onAction` via `act()`
- `DataSourcesGrid.config.spec.tsx` + `.spec.mocks.ts` — config hooks with all peer hooks mocked

`frontend/src/shared/hooks/useReactQueryRqlGrid.spec.tsx` — hook with `QueryClientProvider` wrapper.

---

**See also:** [SKILL.md](../SKILL.md) · [troubleshooting.md](./troubleshooting.md)
