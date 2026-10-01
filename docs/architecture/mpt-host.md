# MPT host integration

The frontend is a **single standalone bundle** that runs in one of two
modes depending on how it's loaded. This document defines the two modes,
what differs between them, how the app detects which mode it's in, and how
to consume host-provided state.

## The two modes

### Standalone mode

- **How it happens.** The bundle is loaded directly — its own tab, a
  browser window, or the local dev server. No parent iframe injecting
  anything.
- **What's true.** `globalThis.__MPT__` is `undefined` and stays that way.
  No host bridge, no auth from a host, no `emit`/`listen`. The app is a
  full-page SPA.
- **When it's used.** Local dev, integration tests, direct browser
  navigation, any deployment that isn't the MPT portal.

### Hosted mode (a.k.a. embedded / iframe-as-extension)

- **How it happens.** The MPT portal loads the bundle inside its iframe.
  Around mount time the host injects `globalThis.__MPT__` with the bridge
  API (see [What `__MPT__` provides](#what-__mpt__-provides)).
- **What's true.** `useHasMPTHost()` returns `true`. Host context (auth,
  data, `isRootPage`) is available through the MPT hooks. `emit` /
  `listen` cross the iframe boundary to the host.
- **When it's used.** Production, when the extension is opened from within
  the MPT portal shell.

### At-a-glance comparison

| Feature / API                                     | Standalone      | Hosted                         |
| ------------------------------------------------- | --------------- | ------------------------------ |
| `globalThis.__MPT__`                              | `undefined`     | injected by host (~mount time) |
| `useHasMPTHost()`                                 | `false`         | `true`                         |
| `useIsRootPage()`                                 | `false`         | `true`/`false` per host intent |
| `useMPTAuth()` / `useMPTData()`                   | `undefined`     | populated from host            |
| `useMPTEmit()` / cross-window events              | no-op           | fires to host window           |
| `useNotifyParentChildModal(open)`                 | no-op           | emits `child-modal` events     |
| Layout                                            | full-page SPA   | rendered inside host iframe    |

The key insight: **host presence** and **host intent** are two independent
axes — the first is "is a bridge available?", the second is "what did the
host tell us about this slot?". Detection uses two different hooks (see
[Detecting the mode](#detecting-the-mode)); don't conflate them.

## What `__MPT__` provides

Types live in `frontend/src/global.d.ts` (single source of truth — do not
redeclare):

```ts
declare global {
  var __MPT__:
    | {
        context?: unknown;                                    // host state (auth, data)
        onChange?: (cb: (data: unknown) => void) => void;     // context updates
        emit?: (event: string, data: unknown) => void;        // → host window
        listen?: (event: string, handler: (data?: unknown) => void) => () => void;
      }
    | undefined;
}
```

The shape of `context` (parsed via `MPTContextValue` in
`shared/providers/MPTContextProvider.tsx`) has two branches:

- `auth` — `{ user: { id }, account: { id, type } }`. Who the host says
  is signed in.
- `data` — `{ isRootPage?, sample?, [key]: unknown }`. Free-form payload
  from the host slot config. `isRootPage: true` means the host allocated
  this slot as the top-level page (rare).

## Detecting the mode

Two hooks answer "which mode are we in?" — they mean different things.

### `useHasMPTHost()` — is a host bridge present?

**File:** `frontend/src/shared/providers/MPTContextProvider.tsx`
**Source of truth:** `globalThis.__MPT__ !== undefined`
**Returns `true` when:** the MPT host has injected its global into the
iframe (i.e. hosted mode).
**Use when:** you need to know whether the bridge is available before
calling it — typically inside infra hooks. Example:
`useNotifyParentChildModal` only emits when this is true; without the
guard, `emit()` would silently no-op or throw in standalone mode.

### `useIsRootPage()` — does the host want this slot as the root?

**File:** `frontend/src/shared/providers/MPTContextProvider.tsx`
**Source of truth:** `MPTContextValue.data.isRootPage === true`
**Returns `true` when:** the host has told us via its context payload
that this slot is the root.
**Use when:** behaviour depends on the host's *intent*, not merely on
whether a host is present. Rare.

### Which to pick

| Scenario                                                    | `useHasMPTHost` | `useIsRootPage` |
| ----------------------------------------------------------- | --------------- | --------------- |
| Hosted mode, normal flow                                    | `true`          | `false`         |
| Hosted mode with `isRootPage: true` in context              | `true`          | `true`          |
| Standalone mode (no `__MPT__` within 5s)                    | `false`         | `false`         |

## How detection works internally

`MPTContextProvider.tsx` wraps the app tree. On mount:

- `useHasMPTHost` uses `useSyncExternalStore(subscribeToHost, …)`.
- `subscribeToHost` polls `globalThis.__MPT__` every 50 ms. As soon as
  the global appears the interval clears and the store snapshot flips
  from `false` to `true`; if 5 s pass with no host, a safety timeout
  clears the interval so standalone mode stops polling instead of
  burning CPU forever.
- When `useHasMPTHost` returns `true`, `MPTContextProvider` mounts
  `HostContextBridge` — which reads `useMPTContext()` from
  `@mpt-extension/sdk-react` and republishes it through the local
  `MPTContextStore`. When it returns `false`, the app gets an empty
  context (all `useMPT*` hooks return `undefined`).

### Replacing the polling

The 5s-bounded polling is a workaround because the host doesn't signal
injection completion. If the host team adds a `mpt:ready` window event
(or guarantees `__MPT__` is set before our bundle loads),
`subscribeToHost` can be replaced with a one-shot `addEventListener`.

## Consuming host state

Once the bridge is up, four hooks read from the local `MPTContextStore`:

- `useMPT()` — the full `MPTContextValue`.
- `useMPTAuth()` — `MPTAuth | undefined`.
- `useMPTData()` — `MPTData | undefined`.
- `useIsRootPage()` — `boolean` (`data?.isRootPage ?? false`).

All four safely return `undefined` / `false` in standalone mode. Reading
them is always safe; **calling into the bridge** (emitting events, etc.)
is not — gate on `useHasMPTHost()` first.

## Common mistakes

- Using `useIsRootPage` to gate host-only side effects. Host *presence*
  is the right signal there; use `useHasMPTHost`. `isRootPage` is a
  business flag, not a "we have a bridge" flag.
- Calling `emit()` (or any MPT SDK bridge) without checking
  `useHasMPTHost()` first. In standalone the SDK's `emit` is a no-op at
  best; explicit gating documents intent and prevents the "why isn't
  the host reacting?" debugging trip.
- Redeclaring `__MPT__`. There's one declaration in `global.d.ts`;
  duplicating it in another module causes type drift.
