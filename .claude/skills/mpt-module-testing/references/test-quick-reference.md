# Test Patterns Quick Reference

1-page cheat sheet for testing patterns and mocking rules in `ffc-extension/frontend/`.

Stack: `jest@30` + `@swc/jest` (CJS) + `jest-environment-jsdom` + `@testing-library/react@16`.

---

## Critical Rules

### ✅ DO

- Use `.spec.tsx` extension (NOT `.test.tsx`)
- Mock with classic `jest.mock(path, factory)` — SWC hoists it above `import` in CJS mode
- Mock design system using the FULL path: `@swo/design-system/[component]`
- Mock only the runtime exports the SUT uses (type-only exports are erased)
- Use `function` keyword for test setup functions
- Use `@testing-library/react` for component tests
- Wrap state-changing callbacks (invoked directly from test) in `act(...)`

### ❌ DON'T

- Mock `react` or `react-dom`
- Mock design system as `@swo/[component]` (source imports use the full `/design-system/` path)
- Spread `...jest.requireActual("@swo/design-system/...")` inside a mock factory (heap OOM)
- Use `require()` in tests
- Mock modules already stubbed in `jest.setup.js` (`useFixedT`, `@swo/design-system/utils`, `react-i18next`, `react-router-dom`, `@mpt-extension/sdk`)
- Add test-specific code to production files

---

## File Naming

| Test Type | Extension   | Example               |
| --------- | ----------- | --------------------- |
| Component | `.spec.tsx` | `Journal.spec.tsx`    |
| Hook      | `.spec.tsx` | `useColumns.spec.tsx` |
| Utility   | `.spec.ts`  | `formatDate.spec.ts`  |

---

## Pre-Mocked Modules

Already mocked in `frontend/jest.setup.js` — DO NOT mock again:

```
react-router-dom          (Link only; other exports pass through)
react-i18next             (useTranslation returns identity t)
~shared/hooks/useFixedT   (returns identity function)
@swo/design-system/utils  (useDesignSystemOptions, useLocalisation, DisplayValue)
@mpt-extension/sdk        (setup, http — {virtual: true}; package ships ESM-only)
```

Global stubs: `TextEncoder` / `TextDecoder` on `globalThis` (required by `react-router-dom` under jsdom).

---

## Mock Pattern

```typescript
// jest.mock is hoisted above the `import` line by @swc/jest
import { DataSourcesGrid } from "./DataSourcesGrid";

jest.mock("@swo/design-system/grid", () => ({
  Grid: (props: unknown) => <div data-testid="grid" />,
  useGridAsync: jest.fn(),
  GridCellSimple: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));
```

Factory variables that need to be referenced from inside `jest.mock` must start with `mock` (Jest guardrail):

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

## Design System Mocking

### ✅ Correct Pattern (ffc-extension)

```typescript
// Full path — matches source imports in this repo
jest.mock("@swo/design-system/grid", () => ({
  Grid: ({ columns, fields }: any) => (
    <div data-testid="grid">
      <div data-testid="grid-columns">{JSON.stringify(columns)}</div>
      <div data-testid="grid-fields">{JSON.stringify(fields)}</div>
    </div>
  ),
}));

jest.mock("@swo/design-system/entity-reference-cell", () => ({
  EntityReferenceCell: ({ primaryContent, secondaryContent }: any) => (
    <div data-testid="entity-reference-cell">
      <span>{primaryContent}</span>
      <span>{secondaryContent}</span>
    </div>
  ),
}));
```

### ❌ Incorrect Patterns

```typescript
// ❌ Wrong path — source uses full "@swo/design-system/grid", not "@swo/grid"
jest.mock("@swo/grid", () => ({ ... }));

// ❌ Heap OOM — spreads the entire real design-system graph
jest.mock("@swo/design-system/grid", () => ({
  ...jest.requireActual("@swo/design-system/grid"),
  buildRqlQuery: jest.fn(),
}));
```

---

## Component Test Structure

```typescript
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { MyComponent } from "./MyComponent";

const mockList = jest.fn();
jest.mock("~organizations/api", () => ({
  useOrganizationsApi: () => ({ list: mockList }),
}));

jest.mock("@swo/design-system/grid", () => ({
  Grid: ({ columns }: any) => (
    <div data-testid="grid">{JSON.stringify(columns)}</div>
  ),
}));

// Test setup function
function renderComponent(props = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MyComponent {...props} />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('MyComponent', () => {
  const mockApi = {
    baseQueryKey: jest.fn(() => ['api', '/api/mymodules']),
    list: jest.fn(),
    get: jest.fn(),
    save: jest.fn(),
  };

  beforeEach(() => {
    (useMyModuleApi as jest.Mock).mockReturnValue(mockApi);
  });

  it('renders component', () => {
    renderComponent();
    expect(screen.getByTestId('grid')).toBeInTheDocument();
  });

  it('loads data on mount', async () => {
    mockApi.list.mockResolvedValue([{ id: '1', name: 'Test' }]);

    renderComponent();

    await waitFor(() => {
      expect(mockApi.list).toHaveBeenCalled();
    });
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    renderComponent();

    const button = screen.getByRole('button', { name: 'Save' });
    await user.click(button);

    expect(mockApi.save).toHaveBeenCalled();
  });
});
```

---

## Grid Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import { MyModuleGrid } from './MyModule.Grid';
import { useMyModuleApi } from '@/api/useMyModuleApi';
import { useColumns } from './Hooks/useColumns';
import { useFields } from './Hooks/useFields';

jest.mock('@/api/useMyModuleApi');
jest.mock('./Hooks/useColumns');
jest.mock('./Hooks/useFields');
jest.mock('@swo/grid', () => ({
  Grid: ({ data, columns, fields }: any) => (
    <div data-testid="grid">
      <div data-testid="data">{JSON.stringify(data)}</div>
      <div data-testid="columns">{JSON.stringify(columns)}</div>
    </div>
  ),
}));

function renderGrid() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MyModuleGrid />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('MyModuleGrid', () => {
  const mockApi = {
    baseQueryKey: jest.fn(() => ['api', '/api/mymodules']),
    list: jest.fn(),
  };

  beforeEach(() => {
    (useMyModuleApi as jest.Mock).mockReturnValue(mockApi);
    (useColumns as jest.Mock).mockReturnValue([]);
    (useFields as jest.Mock).mockReturnValue([]);
  });

  it('renders grid', () => {
    renderGrid();
    expect(screen.getByTestId('grid')).toBeInTheDocument();
  });

  it('displays data', async () => {
    const data = [{ id: '1', name: 'Test' }];
    mockApi.list.mockResolvedValue(data);

    renderGrid();

    await waitFor(() => {
      const dataElement = screen.getByTestId('data');
      expect(dataElement).toHaveTextContent(JSON.stringify(data));
    });
  });
});
```

---

## Details Container Tests

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { MyModuleDetailsContainer } from './MyModule.Details.Container';
import { useMyModuleApi } from '@/api/useMyModuleApi';

jest.mock('@/api/useMyModuleApi');
jest.mock('./MyModule.Details.Provider', () => ({
  MyModuleDetailsProvider: ({ entity }: any) => (
    <div data-testid="provider">{entity.name}</div>
  ),
}));
jest.mock('@swo/feedback', () => ({
  LoadingSpinner: () => <div data-testid="loading">Loading...</div>,
  ErrorPanel: ({ error }: any) => <div data-testid="error">{error.message}</div>,
}));

// Mock useParams
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ id: 'test-id' }),
}));

function renderContainer() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MyModuleDetailsContainer />
    </QueryClientProvider>
  );
}

describe('MyModuleDetailsContainer', () => {
  const mockApi = {
    baseQueryKey: jest.fn(() => ['api', '/api/mymodules']),
    get: jest.fn(),
  };

  beforeEach(() => {
    (useMyModuleApi as jest.Mock).mockReturnValue(mockApi);
  });

  it('shows loading state', () => {
    mockApi.get.mockReturnValue(new Promise(() => {})); // Never resolves

    renderContainer();

    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });

  it('loads and displays entity', async () => {
    const entity = { id: 'test-id', name: 'Test Entity' };
    mockApi.get.mockResolvedValue(entity);

    renderContainer();

    await waitFor(() => {
      expect(screen.getByTestId('provider')).toHaveTextContent('Test Entity');
    });
  });

  it('shows error state', async () => {
    mockApi.get.mockRejectedValue(new Error('API Error'));

    renderContainer();

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('API Error');
    });
  });
});
```

---

## Action Tests

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeleteAction } from './MyModule.Details.Actions.Delete';
import { useEntity } from '../Hooks/useEntity';
import { useMyModuleApi } from '@/api/useMyModuleApi';

jest.mock('../Hooks/useEntity');
jest.mock('@/api/useMyModuleApi');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

// Mock confirmation dialog
global.confirm = jest.fn();

function renderAction() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <DeleteAction />
    </QueryClientProvider>
  );
}

describe('DeleteAction', () => {
  const mockEntity = { id: 'test-id', name: 'Test' };
  const mockApi = {
    baseQueryKey: jest.fn(() => ['api', '/api/mymodules']),
    remove: jest.fn(),
  };

  beforeEach(() => {
    (useEntity as jest.Mock).mockReturnValue(mockEntity);
    (useMyModuleApi as jest.Mock).mockReturnValue(mockApi);
    (global.confirm as jest.Mock).mockResolvedValue(false);
  });

  it('renders delete button', () => {
    renderAction();
    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });

  it('shows confirmation dialog', async () => {
    const user = userEvent.setup();
    renderAction();

    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(global.confirm).toHaveBeenCalled();
  });

  it('deletes entity when confirmed', async () => {
    (global.confirm as jest.Mock).mockResolvedValue(true);
    mockApi.delete.mockResolvedValue(undefined);

    const user = userEvent.setup();
    renderAction();

    await user.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      expect(mockApi.delete).toHaveBeenCalledWith('test-id');
    });
  });

  it('does not delete when cancelled', async () => {
    (global.confirm as jest.Mock).mockResolvedValue(false);

    const user = userEvent.setup();
    renderAction();

    await user.click(screen.getByRole('button', { name: /delete/i }));

    expect(mockApi.delete).not.toHaveBeenCalled();
  });
});
```

---

## Common Mocking Patterns

### API Hooks

```typescript
jest.mock("@/api/useMyModuleApi", () => ({
  useMyModuleApi: jest.fn(),
}));

const mockApi = {
  baseQueryKey: jest.fn(() => ["api", "/api/mymodules"]),
  list: jest.fn(),
  get: jest.fn(),
  save: jest.fn(),
  remove: jest.fn(),
};

(useMyModuleApi as jest.Mock).mockReturnValue(mockApi);
```

### React Router

```typescript
const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
  useParams: () => ({ id: "test-id" }),
}));
```

### React Query

```typescript
// In test setup
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,        // Disable retries
      cacheTime: 0,        // Disable cache
    },
  },
});

// Wrapper
function Wrapper({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

---

## Troubleshooting

### Test Timeout

```typescript
// Increase timeout for slow tests
jest.setTimeout(10000);

// Or per test
it("slow test", async () => {
  // ...
}, 10000);
```

### Act Warnings

```typescript
// Use waitFor for async updates
await waitFor(() => {
  expect(screen.getByText("Updated")).toBeInTheDocument();
});

// Or wrap in act
await act(async () => {
  await user.click(button);
});
```

### Query Not Updating

```typescript
// Ensure query invalidation in mutation
const mutation = useMutation({
  mutationFn: api.save,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: api.baseQueryKey() });
  },
});

// In test, wait for invalidation
await waitFor(() => {
  expect(mockApi.list).toHaveBeenCalledTimes(2); // Initial + after mutation
});
```

---

## Running Tests

```bash
# Run all tests
npm test

# Run specific file
npm test Journal.spec.tsx

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Update snapshots
npm test -- -u
```

---

**Full Documentation:**

- [Testing Conventions](./testing-conventions.md)
- [Troubleshooting](./troubleshooting.md)
