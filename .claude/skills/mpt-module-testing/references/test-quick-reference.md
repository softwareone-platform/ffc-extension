# Test Patterns Quick Reference

1-page cheat sheet for `ffc-extension/frontend/` unit tests.

Stack: `jest@30` + `@swc/jest` (CJS) + `jest-environment-jsdom` + `@testing-library/react@16`.

---

## Critical Rules

### ✅ DO

- Use `.spec.tsx` extension (NOT `.test.tsx`)
- Mock with classic `jest.mock(path, factory)` — SWC hoists it above `import`
- Mock design system using the FULL path: `@swo/design-system/[component]`
- Mock only the runtime exports the code under test uses (type-only exports are erased)
- Use `function` keyword for test setup functions
- Wrap state-changing callbacks (invoked directly from test) in `act(...)`
- Use `MemoryRouter` + `Routes` + `Route` for `useParams`

### ❌ DON'T

- Mock `react` or `react-dom`
- Mock design system as `@swo/[component]` (source uses the full `/design-system/` path)
- Spread `...jest.requireActual("@swo/design-system/...")` inside a mock factory (heap OOM)
- Mock modules already stubbed in `jest.setup.js` (see Pre-Mocked below)
- Add test-specific code to production files

---

## File Naming

| Test Type | Extension   | Example                |
| --------- | ----------- | ---------------------- |
| Component | `.spec.tsx` | `DataSources.spec.tsx` |
| Hook      | `.spec.tsx` | `useColumns.spec.tsx`  |
| Utility   | `.spec.ts`  | `formatDate.spec.ts`   |

---

## Pre-Mocked Modules (`frontend/jest.setup.js`)

DO NOT mock again: `react-router-dom` (Link only), `react-i18next`, `~shared/hooks/useFixedT`, `@swo/design-system/utils`, `@mpt-extension/sdk`.

Global stubs: `TextEncoder` / `TextDecoder`.

Full details: [SKILL.md → Pre-Mocked Modules](../SKILL.md#pre-mocked-modules-already-in-jestsetupjs--do-not-mock-again).

---

## Mock Pattern

```typescript
import { render, screen } from "@testing-library/react";

import { DataSourcesGrid } from "./DataSourcesGrid";

// jest.mock is hoisted above the import above by @swc/jest
jest.mock("@swo/design-system/grid", () => ({
  Grid: (props: unknown) => <div data-testid="grid" />,
}));
```

Factory variables referenced from inside `jest.mock` must start with `mock` (Jest guardrail):

```typescript
const mockGridProps = jest.fn();
jest.mock("@swo/design-system/grid", () => ({
  Grid: (props: unknown) => {
    mockGridProps(props);
    return <div data-testid="grid" />;
  },
}));
```

---

## Wrapping Patterns

- **`useParams`:** wrap in `MemoryRouter` + `Routes` + `Route path=":organizationId"` (don't mock `useParams`)
- **React Query:** wrap in `QueryClientProvider` with `{ defaultOptions: { queries: { retry: false } } }`

Snippets: see [SKILL.md → Test Wrappers](../SKILL.md#test-wrappers).

---

## Canonical Examples

Copy from — these are the reference specs for this repo:

- `frontend/src/features/organizations/details/data-sources/DataSources.spec.tsx` — container + `MemoryRouter` + child mock
- `frontend/src/features/organizations/details/data-sources/DataSourcesGrid.spec.tsx` — thin Grid wrapper, captured `onAction` invoked via `act()`
- `frontend/src/features/organizations/details/data-sources/DataSourcesGrid.config.spec.tsx` — `useColumns` / `useFields` / `useAsyncOptions` / `useGridConfig` with all peer hooks mocked
- `frontend/src/shared/hooks/useReactQueryRqlGrid.spec.tsx` — hook with `QueryClientProvider` wrapper

---

## Running Tests

```bash
npm test                                   # all tests
npm test -- --testPathPatterns="Foo"       # by pattern
npm run test:coverage                      # coverage report
npm test -- --watch                        # watch mode
```

---

**Full docs:** [testing-conventions.md](./testing-conventions.md) · [troubleshooting.md](./troubleshooting.md)
