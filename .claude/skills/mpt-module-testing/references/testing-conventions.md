# 06: Testing Conventions

This document covers test structure, placement, mocking rules, and common testing patterns for modules in `ffc-extension/frontend/`.

Stack: `jest@30` + `@swc/jest` (CJS transform) + `jest-environment-jsdom` + `@testing-library/react@16`.

Classic `jest.mock(path, factory)` works — SWC hoists it above `import`. Design-system paths must be the full `@swo/design-system/[component]` (see below).

---

## Test File Basics

### File Extension

**CRITICAL:** Always use `.spec.tsx` extension

```
✅ Journal.Grid.spec.tsx
✅ useColumns.spec.tsx
✅ AddWizard.spec.tsx

❌ Journal.Grid.test.tsx      WRONG
❌ useColumns.test.ts         WRONG
```

### Test Co-location

Tests are **always co-located** with source files:

```
Grid/
├── Journal.Grid.tsx
├── Journal.Grid.spec.tsx    ✅ Next to source
└── Hooks/
    ├── useColumns.tsx
    └── useColumns.spec.tsx  ✅ Next to hook
```

---

## Mocking Rules

### Design System Components

**CRITICAL for ffc-extension:** mock design-system components using the FULL `@swo/design-system/[component]` path — that is what the source code imports. Mocking `@swo/[component]` (shortened) is a common trap inherited from other repos: it never intercepts anything.

```typescript
// ✅ CORRECT (ffc-extension)
jest.mock("@swo/design-system/grid", () => ({
  Grid: (props: any) => <div data-testid="grid" {...props}>Grid</div>,
  useGridAsync: jest.fn(),
  GridCellSimple: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@swo/design-system/entity-reference-cell", () => ({
  EntityReferenceCell: ({ primaryContent, secondaryContent }: any) => (
    <div data-testid="entity-reference-cell">
      <span>{primaryContent}</span>
      <span>{secondaryContent}</span>
    </div>
  ),
}));

// ❌ WRONG — shortened path never intercepts (source imports the full path)
jest.mock("@swo/grid", () => ({ ... }));

// ❌ WRONG — spreading the real module blows the heap
jest.mock("@swo/design-system/grid", () => ({
  ...jest.requireActual("@swo/design-system/grid"),
  buildRqlQuery: jest.fn(),
}));
```

**Reason:** in this repo source code imports the full `@swo/design-system/[component]` path — Jest keys the module cache by that ID, so the mock has to match exactly. Return only the runtime exports the SUT uses; type-only exports are erased by SWC.

### Pre-Mocked Modules (ffc-extension `jest.setup.js`)

Already mocked globally — **don't re-mock** in specs:

```typescript
// ✅ Already mocked — use directly
import { useFixedT } from "~shared/hooks/useFixedT";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { useDesignSystemOptions } from "@swo/design-system/utils";
import { http } from "@mpt-extension/sdk";
```

**Pre-mocked modules:**

- `~shared/hooks/useFixedT` (returns identity function)
- `react-i18next` (`useTranslation` returns identity `t`; `Trans` renders `i18nKey`)
- `react-router-dom` (only `Link` is stubbed; other exports pass through — use `MemoryRouter` + `Routes` for route params)
- `@swo/design-system/utils` (`useDesignSystemOptions`, `useLocalisation`, `DisplayValue`)
- `@mpt-extension/sdk` (`{ setup, http }` — declared with `{ virtual: true }` because the package ships ESM-only and `require()` can't resolve it in CJS)

**Global stubs:**

- `TextEncoder` / `TextDecoder` on `globalThis` — jsdom does not provide them natively; `react-router-dom` (v6+) reaches for them at import time, so without this every spec that uses the router crashes with `ReferenceError`.

**Legacy entries (from `mpt-vikings-ui`, IGNORE):**

- `@/Hooks/useFixedT`
- `@swo/user-react` (useUserData)
- Common context providers (check `jest.setup.js`)

### Never Mock

**Never mock** these modules:

```typescript
❌ jest.mock('react');
❌ jest.mock('react-dom');
❌ jest.mock('react-router-dom');  // Mock specific hooks if needed, not entire module
```

---

## Module Tests

### Testing Main Module Routing

```typescript
// Journal.spec.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { Journal } from './Journal';

jest.mock('./Grid', () => ({
  JournalGrid: () => <div data-testid='journal-grid'>Grid</div>,
}));

jest.mock('./Details', () => ({
  JournalDetailsContainer: () => <div data-testid='journal-details'>Details</div>,
}));

describe('Journal', () => {
  it('renders grid at root path', () => {
    render(
      <MemoryRouter initialEntries={['/journals']}>
        <Routes>
          <Route path='/journals/*' element={<Journal />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('journal-grid')).toBeInTheDocument();
  });

  it('renders details at entity path', () => {
    render(
      <MemoryRouter initialEntries={['/journals/123']}>
        <Routes>
          <Route path='/journals/*' element={<Journal />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('journal-details')).toBeInTheDocument();
  });
});
```

---

## Grid Component Tests

### Testing Grid View

```typescript
// Journal.Grid.spec.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { JournalGrid } from './Journal.Grid';

jest.mock('@swo/grid', () => ({
  Grid: (props: any) => <div data-testid='grid'>Grid</div>,
}));

jest.mock('@swo/card', () => ({
  Card: ({ children }: any) => <div data-testid='card'>{children}</div>,
}));

jest.mock('./Journal.Grid.config', () => ({
  useGridConfig: jest.fn().mockReturnValue({
    silentRefresh: jest.fn(),
    onEvent: jest.fn(),
    columns: [],
    fields: [],
  }),
}));

describe('JournalGrid', () => {
  it('renders grid component', () => {
    render(
      <MemoryRouter>
        <JournalGrid />
      </MemoryRouter>
    );

    expect(screen.getByTestId('grid')).toBeInTheDocument();
  });

  it('renders add button', () => {
    render(
      <MemoryRouter>
        <JournalGrid />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: /add/i })).toBeInTheDocument();
  });
});
```

### Testing Grid Config Hook

```typescript
// Journal.Grid.config.spec.tsx
import { renderHook } from "@testing-library/react";
import { useGridConfig } from "./Journal.Grid.config";

jest.mock("./Hooks/useColumns", () => ({
  useColumns: jest.fn().mockReturnValue([]),
}));

jest.mock("./Hooks/useFields", () => ({
  useFields: jest.fn().mockReturnValue([]),
}));

jest.mock("@swo/grid", () => ({
  useGridAsync: jest.fn((options) => options),
  useGridIdentity: jest.fn(() => ({ identity: "journals" })),
}));

describe("useGridConfig", () => {
  it("returns grid configuration", () => {
    const { result } = renderHook(() => useGridConfig());

    expect(result.current).toHaveProperty("columns");
    expect(result.current).toHaveProperty("fields");
  });
});
```

### Testing useColumns Hook

```typescript
// useColumns.spec.tsx
import { renderHook } from "@testing-library/react";
import { useColumns } from "./useColumns";

describe("useColumns", () => {
  it("returns column definitions", () => {
    const { result } = renderHook(() => useColumns());

    expect(result.current).toHaveLength(5);
    expect(result.current[0]).toEqual({
      name: "journal",
      title: expect.any(String),
      fields: expect.any(Array),
      cell: expect.any(Function),
      initialWidth: expect.any(Number),
      isPinned: true,
    });
  });

  it("has unique column names", () => {
    const { result } = renderHook(() => useColumns());
    const names = result.current.map((col) => col.name);
    const uniqueNames = new Set(names);

    expect(names.length).toBe(uniqueNames.size);
  });
});
```

---

## Details Component Tests

### Testing Details Container

```typescript
// Journal.Details.Container.spec.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { JournalDetailsContainer } from './Journal.Details.Container';

const mockJournal = {
  id: '123',
  journal: 'TEST-001',
  status: 'Draft',
  amount: 100,
  currency: 'USD',
};

jest.mock('./Journal.Details', () => ({
  JournalDetails: () => <div data-testid='journal-details'>Details</div>,
}));

jest.mock('@/api/useJournalApi', () => ({
  useJournalApi: () => ({
    get: jest.fn().mockResolvedValue({ data: mockJournal }),
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

describe('JournalDetailsContainer', () => {
  it('shows loader initially', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/journals/123']}>
          <Routes>
            <Route path='/journals/:journalId' element={<JournalDetailsContainer />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByTestId('loader')).toBeInTheDocument();
  });

  it('renders details after loading', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/journals/123']}>
          <Routes>
            <Route path='/journals/:journalId' element={<JournalDetailsContainer />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('journal-details')).toBeInTheDocument();
    });
  });
});
```

### Testing Details Components

```typescript
// Journal.Details.spec.tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { JournalDetails } from './Journal.Details';

jest.mock('./Hooks/useJournal', () => ({
  useJournal: () => ({
    entity: mockJournal,
    refreshEntity: jest.fn(),
  }),
}));

jest.mock('@swo/design-system/navigation', () => ({
  Navigation: {
    TopBar: ({ children }: any) => <div>{children}</div>,
  },
}));

describe('JournalDetails', () => {
  it('renders details content', () => {
    render(
      <MemoryRouter initialEntries={['/journals/123/details']}>
        <JournalDetails />
      </MemoryRouter>
    );

    expect(screen.getByText(/TEST-001/i)).toBeInTheDocument();
  });
});
```

### Testing Entity Hook

```typescript
// useJournal.spec.tsx
import { renderHook } from '@testing-library/react';
import { useJournal } from './useJournal';
import { DetailsProvider } from '@/Components/DetailsProvider';

const mockValue = {
  entity: { id: '123', journal: 'TEST-001' },
  refreshEntity: jest.fn(),
};

describe('useJournal', () => {
  it('returns entity from provider', () => {
    const wrapper = ({ children }: any) => (
      <DetailsProvider value={mockValue}>{children}</DetailsProvider>
    );

    const { result } = renderHook(() => useJournal(), { wrapper });

    expect(result.current.entity).toEqual(mockValue.entity);
    expect(result.current.refreshEntity).toBe(mockValue.refreshEntity);
  });
});
```

---

## API Hook Tests

### Testing API Hooks

```typescript
// useJournalApi.spec.tsx
import { renderHook } from "@testing-library/react";
import { useJournalApi } from "./useJournalApi";

jest.mock("./useEntityApi", () => ({
  useBillingEntityApi: jest.fn(() => ({
    get: jest.fn(),
    save: jest.fn(),
    remove: jest.fn(),
    list: jest.fn(),
  })),
  useEntityActionCall: jest.fn(() => ({
    submit: jest.fn(),
    regenerate: jest.fn(),
    reset: jest.fn(),
  })),
}));

describe("useJournalApi", () => {
  it("returns all api methods", () => {
    const { result } = renderHook(() => useJournalApi());

    expect(result.current.get).toBeDefined();
    expect(result.current.save).toBeDefined();
    expect(result.current.delete).toBeDefined();
    expect(result.current.submit).toBeDefined();
    expect(result.current.regenerate).toBeDefined();
  });
});
```

---

## Common Test Patterns

### Pattern: Testing with Router

```typescript
const renderWithRouter = (component: ReactElement, initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path='*' element={component} />
      </Routes>
    </MemoryRouter>
  );
};
```

### Pattern: Testing with React Query

```typescript
const renderWithQuery = (component: ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};
```

### Pattern: Testing User Interactions

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('handles button click', async () => {
  const onClick = jest.fn();
  render(<AddButton onClick={onClick} />);

  const button = screen.getByRole('button');
  await userEvent.click(button);

  expect(onClick).toHaveBeenCalledTimes(1);
});
```

### Pattern: Testing Async Operations

```typescript
it('handles async action', async () => {
  const submitMock = jest.fn().mockResolvedValue({ data: {} });

  jest.mock('@/api/useJournalApi', () => ({
    useJournalApi: () => ({ submit: submitMock }),
  }));

  render(<DetailsActions />);

  const submitButton = screen.getByText(/submit/i);
  await userEvent.click(submitButton);

  await waitFor(() => {
    expect(submitMock).toHaveBeenCalledWith({ id: '123' });
  });
});
```

---

## Test Coverage

### What to Test

**Do test:**

- ✅ Component renders without errors
- ✅ Correct props passed to children
- ✅ User interactions trigger expected behavior
- ✅ Conditional rendering based on state/props
- ✅ Hook return values
- ✅ API integration logic
- ✅ State transitions

**Don't test:**

- ❌ Implementation details
- ❌ Third-party library internals
- ❌ CSS/styling (unless functional requirement)
- ❌ Trivial code (getters/setters)

---

## Copilot Usage Tips

### Generating Tests

```
@workspace Generate tests for Journal.Grid.tsx following test conventions
Create test file for useColumns hook with proper mocking
Generate Details Container tests with React Query setup
```

### Finding Test Patterns

```
@workspace Show me test mocking patterns for design system components
Find examples of testing grid components with actions
How are API hooks tested in existing modules?
```

### Fixing Test Issues

```
@workspace Fix design system mocking - should use @swo/grid not @swo/design-system/grid
Help debug failing test for Journal.Details.Container
```

---

## Common Test Errors

### Error: Cannot find module '@swo/design-system/grid'

**Cause:** Incorrect mock path

```typescript
// ❌ Wrong
jest.mock('@swo/design-system/grid', () => ({...}));

// ✅ Correct
jest.mock('@swo/grid', () => ({...}));
```

### Error: useFixedT is not a function

**Cause:** Hook already mocked in jest.setup.js, conflicting mock

```typescript
// ❌ Don't do this
jest.mock('@/Hooks/useFixedT', () => ({...}));

// ✅ Use directly (already mocked)
import { useFixedT } from '@/Hooks/useFixedT';
```

### Error: Cannot read property 'data' of undefined

**Cause:** Missing React Query provider

```typescript
// ✅ Add QueryClientProvider
render(
  <QueryClientProvider client={queryClient}>
    <Component />
  </QueryClientProvider>
);
```

---

## Related Documentation

- **Testing Library docs**: https://testing-library.com/docs/react-testing-library/intro
- **Jest docs**: https://jestjs.io/docs/getting-started
- **Test patterns reference**: [quick-reference/test-patterns.md](quick-reference/test-patterns.md)
- **Code examples**: [examples/code-snippets.md](examples/code-snippets.md)

---

**Next Step:** Review [07-code-style-guidelines.md](07-code-style-guidelines.md) for code style and commit conventions.
