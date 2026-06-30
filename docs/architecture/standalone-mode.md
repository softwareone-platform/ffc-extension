# Standalone mode flags

There are **three** different "am I standalone?" signals in this codebase.
They mean different things and have different sources of truth. Pick the
right one or behavior will diverge between embedded and standalone runs.

## The three hooks

### `useHasMPTHost()`
**File:** `frontend/src/shared/providers/MPTContextProvider.tsx`
**Source of truth:** `globalThis.__MPT__ !== undefined`
**Returns `true` when:** the MPT host has injected its global into the iframe.
**Use when:** you need to know whether a host bridge is available — typically
inside other infra hooks (e.g. `useNotifyParentChildModal` only emits when
this is true).

### `useIsRoot()`
**File:** `frontend/src/shared/providers/MPTContextProvider.tsx`
**Source of truth:** `MPTContextValue.data.isRoot === true` (set by
the host via `globalThis.__MPT__.context`).
**Returns `true` when:** the host has told us this slot is the root slot
via its MPT data payload.
**Use when:** behavior depends on the host's intent, not on whether the host
is present. Rare.

### `useIsStandaloneShell()`
**File:** `frontend/src/shared/providers/StandaloneShellContext.tsx`
**Source of truth:** a React context populated by `<StandaloneShellProvider>`
(currently wrapped around `MainLayout`).
**Returns `true` when:** the component tree is rendered under the standalone
shell layout — i.e. `MainLayout` is the active layout.
**Use when:** UI varies depending on which layout shell is rendering (e.g.
`UsersGrid` shows a custom standalone modal in shell mode, vs. opening an MPT
modal entry when embedded).

## How they differ in practice

| Scenario | `useHasMPTHost` | `useIsRoot` | `useIsStandaloneShell` |
|---|---|---|---|
| App loaded inside MPT host iframe, normal flow | `true` | `false` | `false` |
| App loaded inside MPT host with `isRoot: true` in data | `true` | `true` | depends on route |
| App loaded directly (no host injection within 5s) | `false` | `false` | depends on route |
| Component rendered under `MainLayout` | independent | independent | `true` |

The key insight: **host presence**, **host intent**, and **active layout
shell** are three independent axes. Don't conflate them — a component can be
inside the standalone shell while still having a host bridge available.

## Common mistakes

- Using `useIsRoot` to decide whether to show a standalone-styled
  modal. The standalone *shell* is the right signal; use `useIsStandaloneShell`.
- Using `useIsStandaloneShell` to decide whether to call `emit()` from the MPT
  SDK. The SDK only works with a host bridge; gate on `useHasMPTHost` instead.

## See also

- [MPT host integration](./mpt-host-integration.md) — how `__MPT__` gets
  injected and how we detect it.
