# API hook conventions

Two distinct hook shapes coexist in `frontend/src/features/*/api/`. They're
not interchangeable — pick by purpose.

> **Sandbox note:** on this branch the `useFooApi` implementations return
> **static mock data** (`api/mockData.ts` wrapped by `~shared/utils/mockResponse`)
> instead of hitting the backend. The *shape/contract* below is unchanged —
> only the transport is stubbed.

## `useFooApi.tsx` — data-source callbacks

Returns memoized callbacks that resolve to an axios-shaped response. No React
Query, no caching, no state.

```ts
export function useOrganizationsApi() {
  const list = useCallback(/* GET /ops/v1/organizations */, []);
  const get  = useCallback(/* GET /ops/v1/organizations/:id */, []);
  // ...
  return useMemo(() => ({ list, get, /* ... */ }), [list, get /* ... */]);
}
```

**Use for:**
- Imperative calls (e.g. inside a `useEffect`, a form `onSubmit`, or a mutation).
- The building block for `useFooDetailsApi.ts` (see below).

Grids no longer fetch through these hooks — they render static rows with
`useGridInMemory(mockData, config)` (see any `*Grid.config.tsx`), so a `list()`
callback is only kept where something still consumes it.

**Naming:** `useFooApi.tsx` (or `.ts` if no JSX). Returns `{ list, get, ... }`
where each member is an async function returning an axios response.

## `useFooDetailsApi.ts` — `useQuery` wrappers for a single entity

Wraps `useQuery` with a **stable, conventional query key** and the matching
`useFooApi().get()` call. Returns the full React Query result.

```ts
export function useOrganizationDetailsApi(organizationId: string | undefined) {
  const { get } = useOrganizationsApi();
  return useQuery({
    queryKey: ["Organizations", "Details", organizationId] as const,
    queryFn: () => get(organizationId!),
    select: (res) => res.data,
    enabled: Boolean(organizationId),
  });
}
```

**Use for:** any component rendering a detail view of one entity. React Query
dedupes the request across components that all call this hook with the same
id — header, body, side panels all share one fetch.

**Don't inline `useQuery` in components.** If the detail hook doesn't exist
for an entity yet, add it to the entity's `api/` folder instead. This is the
single source for the query key — inlining risks key drift, duplicate
requests, and broken cache invalidation.

## Query key convention

`["<EntityName>", "<Slice>", ...identifiers]` — e.g.:

- `["Organizations", "Details", organizationId]`
- `["Entitlements", "Details", entitlementId]`

Always `as const` so the key tuple stays narrow. Order matters: invalidating
`["Organizations"]` should refresh every Organizations subtree.

## File layout

```
features/<entity>/api/
├── index.ts                  # barrel
├── useFooApi.tsx             # raw callbacks
└── useFooDetailsApi.ts       # useQuery for single entity
```

The barrel re-exports both. Consumers import from the barrel:

```ts
import { useOrganizationsApi, useOrganizationDetailsApi } from "~organizations/api";
```

## See also

- [i18n conventions](./i18n.md) — the `["Entity", "Slice", ...]` query-key shape loosely mirrors the i18n `<feature>:<section>:...` namespace nesting; keep them aligned when adding a new entity.
- [Naming conventions](./naming.md) — file & folder casing for the `features/<entity>/api/` tree.
