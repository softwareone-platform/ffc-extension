# MPT host integration (iframe-as-extension)

The frontend can run two ways: **embedded** inside the MPT host shell, or
**standalone**. The host injects `globalThis.__MPT__` into the iframe around
mount time. This document explains how the React tree detects which mode it's
in and how it talks back to the host.

## Pieces

- `frontend/src/global.d.ts` — types `globalThis.__MPT__` (single source of
  truth; do not redeclare elsewhere).
- `frontend/src/shared/providers/MPTContextProvider.tsx` — polls for
  `__MPT__` via `useSyncExternalStore`, with a 5s safety timeout so standalone
  mode doesn't poll forever. Exposes `useHasMPTHost()` (also re-used by other
  hooks) and `MPTContextProvider` which switches between an empty provider
  (standalone) and `HostContextBridge` (embedded).
- `frontend/src/shared/hooks/useNotifyParentChildModal.ts` — when this app
  opens a child modal inside the iframe, it emits a `child-modal` event so the
  host can dim its own header. A single effect handles open/close *and* the
  unmount-while-open case via React's effect cleanup.

## Detection: how `useHasMPTHost` works

`subscribeToHost` polls `globalThis.__MPT__` every 50ms. As soon as it appears,
the interval clears and `onChange()` fires so `useSyncExternalStore` flips its
snapshot from `false` to `true`. After 5 seconds with no host, a safety timeout
clears the interval — standalone mode stops polling instead of burning CPU
forever.

## Replacing the polling

The 5s-bounded polling is a workaround because the host doesn't currently
signal injection completion. If the host team adds a `mpt:ready` window event
(or guarantees `__MPT__` is set before our bundle loads), `subscribeToHost` can
be replaced with a one-shot `addEventListener`. See the message draft in the
team's host-integration thread for the proposed contract.

## See also

- [Standalone mode flags](./standalone-mode.md) — the three different
  "am I standalone?" hooks and when to use each.
