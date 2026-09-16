# 10: Troubleshooting

This document covers common issues when writing unit tests in `ffc-extension/frontend/` and their solutions.

---

## ffc-extension specifics (READ FIRST)

The pitfalls unique to this repo's Jest setup (CJS + `@swc/jest` + jsdom):

### Problem: `Cannot find module '@mpt-extension/sdk' from ...`

**Cause:** `@mpt-extension/sdk`'s `package.json` declares only `"exports": { ".": { "import": "./dist/index.js" } }`. In Jest's CJS mode `require()` refuses to resolve packages that expose only the `import` condition.

**Solution:** already stubbed globally in `frontend/jest.setup.js` with `{ virtual: true }`:

```javascript
jest.mock('@mpt-extension/sdk', () => ({
  setup: jest.fn(),
  http: jest.fn(),
}), { virtual: true });
```

If you see the error, verify the stub is still in `jest.setup.js`. Do not add a per-spec workaround. `virtual: true` is mandatory — without it Jest first tries to resolve the module on disk and crashes.

### Problem: `ReferenceError: TextEncoder is not defined` when importing `react-router-dom`

**Cause:** jsdom (used as `testEnvironment`) does not provide `TextEncoder` / `TextDecoder` globally. `react-router-dom` (v6+) touches `TextEncoder` at import time, so any spec that renders under `MemoryRouter` — or that transitively triggers `jest.requireActual('react-router-dom')` from `jest.setup.js` — crashes on module load.

**Solution:** already stubbed globally in `frontend/jest.setup.js`:

```javascript
import {TextEncoder, TextDecoder} from 'node:util';
Object.assign(globalThis, {TextEncoder, TextDecoder});
```

### Problem: `Jest encountered an unexpected token ... export {}` from a `node_modules` package

**Symptom:** Jest tries to run an ESM-only file from `@swo/…`, `@tanstack/…`, `axios`, `zod`, `@mpt-extension/…`, etc. and dies on `export`/`import` syntax.

**Cause:** by default Jest ignores `node_modules` when transforming. If a dependency ships ESM without a CJS fallback, that raw ESM leaks into the test runtime.

**Solution:** the config already includes those packages in `transformIgnorePatterns` so SWC transpiles them to CJS:

```javascript
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

```typescript
import { act } from "@testing-library/react";

const onAction = mockUseGridConfig.mock.calls[0][1];
act(() => onAction("force_import", item));

expect(mockForceImportModal.mock.calls.at(-1)![0]).toMatchObject({ isOpen: true });
```

---

## Design System Mocking Issues

### Problem: Mock not applied to a design-system component

**Symptom:** the real component renders and you can't find the mock's `data-testid`.

**Cause:** the mock path doesn't match the source import. In `ffc-extension/frontend` source code imports from `@swo/design-system/[component]` (full path), NOT `@swo/[component]` — Jest treats them as distinct module IDs, so a mock on the shorter path never intercepts anything.

**❌ Wrong (pattern from `mpt-vikings-ui`, wrong for this repo):**

```typescript
jest.mock("@swo/grid", () => ({
  Grid: () => <div>Grid</div>,
}));
```

**✅ Solution — use the exact path the source imports:**

```typescript
jest.mock("@swo/design-system/grid", () => ({
  Grid: () => <div>Grid</div>,
}));
```

**Apply to all design-system imports:**

- `@swo/design-system/grid` (not `@swo/grid`)
- `@swo/design-system/entity-reference-cell`
- `@swo/design-system/modal`
- `@swo/design-system/utils` (already mocked in `jest.setup.js` — don't mock again)

### Problem: Heap OOM when spreading the real design-system module inside a mock factory

**Symptom:** `FATAL ERROR: Reached heap limit Allocation failed` when a spec starts. Stack trace points at a factory calling `jest.requireActual("@swo/design-system/…")`.

**Cause:** `@swo/design-system/grid` and siblings are huge modules with heavy side effects. Spreading the real module inside a mock factory pulls the entire dependency graph into the test process.

**❌ Wrong:**

```typescript
jest.mock("@swo/design-system/grid", () => ({
  ...jest.requireActual("@swo/design-system/grid"),
  buildRqlQuery: jest.fn(),
}));
```

**✅ Solution:** return only the runtime exports the code under test actually uses. Type-only exports (`GridColumnDefinition`, `UseAsyncGridConfig`, etc.) are erased by SWC and don't need to be present:

```typescript
jest.mock("@swo/design-system/grid", () => ({
  buildRqlQuery: jest.fn(),
}));
```

---

## Import Issues

### Problem: Path alias not resolving

**Symptom:**

```
Cannot find module '@/api/useJournalApi'
```

**Causes:**

1. Missing path alias configuration in `tsconfig.json`
2. IDE not recognizing TypeScript config

**✅ Solution:**

1. **Check tsconfig.json:**

   ```json
   {
     "compilerOptions": {
       "baseUrl": ".",
       "paths": {
         "@/*": ["src/*"]
       }
     }
   }
   ```

2. **Reload IDE:**
   - VS Code: `Cmd/Ctrl + Shift + P` → "Reload Window"

3. **Verify file exists at expected path:**
   ```
   src/api/useJournalApi.ts  ← Must exist
   ```

### Problem: Relative imports becoming incorrect after file move

**Symptom:**

```
import { useColumns } from '../../../Hooks/useColumns';  // Wrong depth
```

**✅ Solution:**

```typescript
// Use absolute imports
import { useColumns } from "./Hooks/useColumns"; // Relative from current folder
// OR
import { useColumns } from "@/Modules/Journal/Grid/Hooks/useColumns"; // Absolute
```

---

## Testing Issues

### Problem: Pre-mocked module being mocked again

**Symptom:**

```
Warning: Duplicate mock for '@/Hooks/useFixedT'
```

**Cause:** Module already mocked in `jest.setup.js`

**❌ Wrong:**

```typescript
jest.mock("@/Hooks/useFixedT", () => ({
  useFixedT: () => (key: string) => key,
}));
```

**✅ Solution:**
Remove the mock entirely - use the pre-mocked version from `jest.setup.js`.

**Pre-mocked modules in `frontend/jest.setup.js` (ffc-extension):**

- `react-router-dom` (only `Link`; other exports pass through)
- `react-i18next` (`useTranslation` returns identity `t`; `Trans` renders `i18nKey`)
- `~shared/hooks/useFixedT` (returns identity function)
- `@swo/design-system/utils` (`useDesignSystemOptions`, `useLocalisation`, `DisplayValue`)
- `@mpt-extension/sdk` (stub `{ setup, http }` with `{ virtual: true }`; ESM-only package)

Global stubs:

- `TextEncoder` / `TextDecoder` on `globalThis` (required by `react-router-dom` under jsdom)

### Problem: Component not rendering in tests

**Symptom:**

```
Unable to find element with text "Expected Text"
```

**Causes:**

1. Missing routing context
2. Missing React Query provider
3. Component not properly mocked

**✅ Solutions:**

**1. Add Router:**

```typescript
import { MemoryRouter } from 'react-router-dom';

render(
  <MemoryRouter>
    <Component />
  </MemoryRouter>
);
```

**2. Add QueryClient:**

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

render(
  <QueryClientProvider client={queryClient}>
    <Component />
  </QueryClientProvider>
);
```

**3. Check mocks:**

```typescript
// Verify child components are mocked
jest.mock('./Journal.Details', () => ({
  JournalDetails: () => <div data-testid='journal-details'>Details</div>,
}));
```

### Problem: Async tests timing out

**Symptom:**

```
Timeout - Async callback was not invoked within the 5000 ms timeout
```

**✅ Solution:**

**1. Use waitFor:**

```typescript
import { waitFor } from "@testing-library/react";

await waitFor(() => {
  expect(screen.getByTestId("content")).toBeInTheDocument();
});
```

**2. Mock async operations:**

```typescript
jest.mock("@/api/useJournalApi", () => ({
  useJournalApi: () => ({
    get: jest.fn().mockResolvedValue({ data: mockData }),
  }),
}));
```

**3. Increase timeout if needed:**

```typescript
it("loads data", async () => {
  // Test code
}, 10000); // 10 second timeout
```

---

## File Naming Issues

### Problem: Test file not discovered

**Symptom:**
Test file exists but Jest doesn't run it

**Cause:** Wrong extension

**❌ Wrong:**

```
Journal.Grid.test.tsx
useColumns.test.ts
```

**✅ Solution:**

```
Journal.Grid.spec.tsx
useColumns.spec.tsx
```

**Pattern:** Always use `.spec.tsx` or `.spec.ts`

### Problem: Module not exporting correctly

**Symptom:**

```
Attempted import error: 'JournalGrid' is not exported from './Grid'
```

**Cause:** Missing or incorrect export in `index.tsx`

**✅ Solution:**

**Check Grid/index.tsx:**

```typescript
export * from "./Journal.Grid";
export * from "./Journal.Grid.config";
```

**Check main Grid file:**

```typescript
export function JournalGrid() {
  // ← Must be exported
  // ...
}
```

---

## React Query Issues

### Problem: Query not refetching after mutation

**Symptom:**
UI not updating after save/delete

**Cause:** Missing query invalidation

**✅ Solution:**

```typescript
const mutation = useMutation({
  mutationFn: (data) => api.save(data),
  onSuccess: () => {
    // Invalidate queries to trigger refetch
    queryClient.invalidateQueries({ queryKey: baseQueryKey });
  },
});
```

**Or use executeAction hook:**

```typescript
const executeAction = useExecuteAction(refreshEntity);
await executeAction(() => api.save(data)); // Auto-invalidates
```

### Problem: Query running when it shouldn't

**Symptom:**
Query executing with undefined ID

**Cause:** Missing `enabled` option

**✅ Solution:**

```typescript
const { data } = useQuery({
  queryKey: ["Journal", id],
  queryFn: () => get(id!),
  enabled: !!id, // ← Only run when ID exists
});
```

---

## React Hooks Issues

### Problem: Hook called conditionally

**Symptom:**

```
Error: Rendered more hooks than during the previous render
```

**Cause:** Hook inside conditional or loop

**❌ Wrong:**

```typescript
function Component({ showData }: Props) {
  if (showData) {
    const data = useData(); // ← Wrong: Conditional hook
  }
}
```

**✅ Solution:**

```typescript
function Component({ showData }: Props) {
  const data = useData(); // ← Call hook unconditionally

  if (!showData) return null;
  // Use data here
}
```

### Problem: Stale closure in callback

**Symptom:**
Callback uses old value of state/prop

**Cause:** Missing dependency in useCallback

**❌ Wrong:**

```typescript
const handleClick = useCallback(() => {
  console.log(count); // Always logs initial value
}, []); // ← Missing count dependency
```

**✅ Solution:**

```typescript
const handleClick = useCallback(() => {
  console.log(count);
}, [count]); // ← Include dependency
```

---

## Routing Issues

### Problem: Details view not rendering

**Symptom:**
Navigate to `/journals/123` shows nothing

**Causes:**

1. Route path incorrect
2. useParams not extracting ID
3. Component not exported

**✅ Solutions:**

**1. Check route pattern:**

```typescript
<Route path=':journalId/*' element={<JournalDetailsContainer />} />
//           ^^^^^^^^^^^
// Must match useParams name
```

**2. Check useParams:**

```typescript
const { journalId } = useParams(); // ← Name must match route
console.log("ID:", journalId); // Debug
```

**3. Check export:**

```typescript
// Details/index.tsx
export * from "./Journal.Details.Container";
```

### Problem: Nested routes not working

**Symptom:**
Tabs not changing content

**Cause:** Missing trailing `/*` in parent route

**❌ Wrong:**

```typescript
<Route path=':journalId' element={<JournalDetailsContainer />} />
```

**✅ Solution:**

```typescript
<Route path=':journalId/*' element={<JournalDetailsContainer />} />
//                      ^^^ ← Allow nested routes
```

---

## Grid Issues

### Problem: Grid not displaying data

**Symptoms:**

- Empty grid
- Loading forever
- Columns not showing

**Causes & Solutions:**

**1. Missing grid config:**

```typescript
// ✅ Ensure useGridConfig returns all required props
const gridProps = useGridConfig();
console.log("Grid props:", gridProps); // Debug
```

**2. Missing columns:**

```typescript
// ✅ Check useColumns returns array
const columns = useColumns();
console.log("Columns:", columns); // Should have length > 0
```

**3. API not mocked in tests:**

```typescript
// ✅ Mock the API
jest.mock("@/api/useJournalApi", () => ({
  useJournalApi: () => ({
    list: jest.fn().mockResolvedValue({ data: [] }),
  }),
}));
```

### Problem: Async options not loading

**Symptom:**
Dropdown shows no options

**Cause:** Missing async configuration

**✅ Solution:**

```typescript
// useAsyncOptions.ts
return useMemo(
  () => ({
    fieldsWithAsyncOptions: ["accountId"], // ← Must list field
    onAsyncOptionsLoaded: (fieldName, data) => {
      // Transform data to { value, label } format
      return data.map((item) => ({ value: item.id, label: item.name }));
    },
    onAsyncOptionsQuery: async (fieldName, searchTerm) => {
      // Fetch data
      const response = await api.list(query);
      return response.data;
    },
  }),
  [],
);
```

---

## API Integration Issues

### Problem: API method not found

**Symptom:**

```
TypeError: api.submit is not a function
```

**Cause:** Action not included in API hook

**✅ Solution:**

```typescript
// api/useJournalApi.ts
const journalActions = ["submit", "regenerate"] as const;
//                       ^^^^^^ ← Add missing action
```

### Problem: Entity type mismatch

**Symptom:**

```
Property 'customField' does not exist on type 'Journal'
```

**Cause:** Type not extended in TemporaryApiModel

**✅ Solution:**

```typescript
// api/TemporaryApiModel.ts
import * as Swagger from "@swo/mp-api-model/billing";

export interface Journal extends Swagger.Journal {
  customField?: string; // ← Add missing field
}
```

---

## Common Copilot Issues

### Issue: Copilot generates wrong file names

**Problem:** Files named `Journal-Grid.tsx` or `journalGrid.tsx`

**✅ Solution:**

```
Generate Journal.Grid.tsx following naming conventions in /instructions/02-file-naming-conventions.md
```

### Issue: Copilot uses wrong test extension

**Problem:** Creates `.test.tsx` instead of `.spec.tsx`

**✅ Solution:**

```
Create test file for Journal.Grid using .spec.tsx extension following /instructions/06-testing-conventions.md
```

### Issue: Copilot generates unnecessary comments

**Problem:** Too many redundant comments

**✅ Solution:**

```
Generate JournalGrid without comments, following self-documenting code style from /instructions/07-code-style-guidelines.md
```

### Issue: Copilot uses arrow functions for components

**Problem:** `const MyComponent = () => {}`

**✅ Solution:**

```
Generate JournalGrid using function keyword following /instructions/07-code-style-guidelines.md
```

---

## Debug Strategies

### Strategy 1: Console Logging

```typescript
// Add strategic logs
console.log("Entity:", entity);
console.log("Props:", props);
console.log("Query result:", data);

// Log in callbacks
const handleClick = useCallback(() => {
  console.log("Click handler called with:", entity);
}, [entity]);
```

### Strategy 2: React DevTools

1. Install React DevTools browser extension
2. Inspect component props and state
3. Check context values
4. Verify hooks are working

### Strategy 3: Test in Isolation

```typescript
// Create minimal reproduction
function TestComponent() {
  const api = useJournalApi();
  console.log("API methods:", Object.keys(api));
  return null;
}
```

### Strategy 4: Check Network Tab

1. Open browser DevTools
2. Go to Network tab
3. Verify API calls are made
4. Check request/response data

---

## Getting Help

### When Stuck:

1. **Check related documentation:**

   ```
   @workspace Find similar patterns in existing modules
   ```

2. **Search for examples:**

   ```
   @workspace Show me how [specific feature] is implemented
   ```

3. **Review troubleshooting:**

   ```
   @workspace Check /instructions/10-troubleshooting.md for [error]
   ```

4. **Ask Copilot for fixes:**
   ```
   @workspace Fix [specific issue] following project patterns
   Help debug [error message] in [file]
   ```

---

## Prevention Checklist

Before committing code:

- [ ] Tests use `.spec.tsx` extension
- [ ] Mocks use classic `jest.mock` + static `import` (SWC hoists in CJS mode)
- [ ] Design-system mocks use full `@swo/design-system/[component]` path (matching source imports)
- [ ] No re-mocking of modules already stubbed in `jest.setup.js` (`useFixedT`, `@swo/design-system/utils`, `react-i18next`, `react-router-dom`, `@mpt-extension/sdk`)
- [ ] Mock factory returns only the runtime exports the SUT actually uses (avoid `...jest.requireActual(...)` for large design-system modules — OOM risk)
- [ ] State-changing callbacks (invoked directly from test code) wrapped in `act(...)`
- [ ] Functions use `function` keyword not arrow functions
- [ ] No unnecessary comments
- [ ] Imports use `~shared/`, `~organizations/`, `~features/`, `~api/`, `~i18n/`, `~app/` aliases
- [ ] No unused imports/variables
- [ ] `npm test` passes locally
- [ ] TypeScript compiles without errors

---

## Related Documentation

- **File naming**: [02-file-naming-conventions.md](02-file-naming-conventions.md)
- **Testing**: [06-testing-conventions.md](06-testing-conventions.md)
- **Code style**: [07-code-style-guidelines.md](07-code-style-guidelines.md)
- **Quick reference**: [quick-reference/](quick-reference/) folder

---

**Common issue not listed?** Check [GLOSSARY.md](GLOSSARY.md) for term definitions or [examples/code-snippets.md](examples/code-snippets.md) for working code patterns.
