# Host-presence flags

The app ships as a single standalone bundle that can run **inside the MPT host
iframe** or **loaded directly**. Two hooks answer "is a host present, and what
did it tell us?" — they mean different things and have different sources of
truth. Pick the right one or behavior will diverge between the two runs.

## The two hooks

### `useHasMPTHost()`
**File:** `frontend/src/shared/providers/MPTContextProvider.tsx`
**Source of truth:** `globalThis.__MPT__ !== undefined`
**Returns `true` when:** the MPT host has injected its global into the iframe.
**Use when:** you need to know whether a host bridge is available — typically
inside other infra hooks (e.g. `useNotifyParentChildModal` only emits when
this is true).

### `useIsRootPage()`
**File:** `frontend/src/shared/providers/MPTContextProvider.tsx`
**Source of truth:** `MPTContextValue.data.isRootPage === true` (set by the
host via `globalThis.__MPT__.context`).
**Returns `true` when:** the host has told us this slot is the root slot via
its MPT data payload.
**Use when:** behavior depends on the host's intent, not merely on whether the
host is present. Rare.

## How they differ in practice

| Scenario | `useHasMPTHost` | `useIsRootPage` |
|---|---|---|
| App loaded inside MPT host iframe, normal flow | `true` | `false` |
| App loaded inside MPT host with `isRootPage: true` in data | `true` | `true` |
| App loaded directly (no host injection within 5s) | `false` | `false` |

The key insight: **host presence** and **host intent** are independent axes.
Don't conflate them.

## Common mistakes

- Using `useIsRootPage` to gate host-only side effects. Host *presence* is the
  right signal there; use `useHasMPTHost`.
- Calling `emit()` (or any MPT SDK bridge) without gating on `useHasMPTHost` —
  the SDK only works when a host bridge is present.

## See also

- [MPT host integration](./mpt-host-integration.md) — how `__MPT__` gets
  injected and how we detect it.
