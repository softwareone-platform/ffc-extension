# Entry modes

This frontend ships as **multiple independent bundles**, not one SPA. Each
file in `frontend/src/entries/` becomes its own esbuild bundle (see
`frontend/esbuild.config.js` → `entryPoints`). The MPT host loads whichever
bundle it needs, when it needs it.

Three entry shapes are in use today, one helper per shape. All three live in
`frontend/src/app/bootstrap/` and ultimately go through the same `mount()`
function, which delegates to `@mpt-extension/sdk`'s `setup()` so the host
controls where the React root attaches.

## Shapes

### 1. Standalone entry — `mountStandaloneEntry(router)`

Mounts the **full SPA** with React Router. One bundle, all routes.

```ts
// frontend/src/entries/index.tsx
const router = createBrowserRouter([/* ... */]);
mountStandaloneEntry(router);
```

Used by the development standalone build. Wraps the router in `AppProviders`
(i18n + extensions context).

### 2. Feature entry — `mountFeatureEntry(routes)`

Mounts a **single feature's routes** inside a `BrowserRouter`. One bundle
per feature, loaded by the host when that section is opened.

```ts
// frontend/src/entries/Entitlements.tsx
mountFeatureEntry(
  <>
    <Route index element={<EntitlementsGrid />} />
    <Route path={SEGMENTS.idParam} element={<DetailsLayout … />}>
      …
    </Route>
  </>
);
```

Each feature entry currently in use:
- `entries/Organizations.tsx` — Organizations routes.
- `entries/Entitlements.tsx` — Entitlements routes.

### 3. Modal entry — `mountModalEntry(<Modal />)`

Mounts a **single modal component** (no router). The host opens these by id
through the MPT SDK (e.g. `open("finops.admin.create-user-modal", { … })`)
and they render in place inside the host chrome.

```ts
// frontend/src/entries/CreateUserModal.tsx
import CreateUserEntryModal from "~organizations/details/users/modal/CreateUserEntryModal";

mountModalEntry(<CreateUserEntryModal />);
```

Modal entry components implement `ModalEntryComponent` (`shared/components/modal/modalEntry.ts`):

```ts
type ModalEntryProps = { onClose?: (result?: { success?: boolean }) => void };
type ModalEntryComponent = ComponentType<ModalEntryProps>;
```

The host supplies `onClose`; the modal calls it with `{ success: true }` on
successful submit, or with no argument on cancel.

## Provider stack

Every entry wraps its content in `AppProviders` → `ExtensionsProvider` (which
itself provides i18n and React Query). Standalone and feature entries add a
router around it; modal entries do not.

```
mount(node)                       // calls SDK setup → createRoot.render
  └─ AppProviders
       └─ ExtensionsProvider      // i18n + React Query
            └─ <entry-specific tree>
```

## Adding a new entry

1. Decide the shape: full SPA / feature / modal.
2. Create `frontend/src/entries/<name>.tsx` and call the appropriate
   `mount*Entry(...)` helper.
3. Add the new file path to `entryPoints` in `frontend/esbuild.config.js`.
4. For modal entries: the modal component itself lives next to its owning
   feature (e.g. `features/entitlements/modal/`,
   `features/organizations/details/users/modal/`), must `export default` a
   `ModalEntryComponent`, and is referenced by id from the host registry.
   See [`docs/conventions/modals.md`](../conventions/modals.md).

## See also

- [MPT host integration](./mpt-host-integration.md) — how the host bridge
  works inside any entry that runs embedded.
- [Standalone mode flags](./standalone-mode.md) — disambiguating
  `useHasMPTHost` / `useIsRootPage` / `useIsStandaloneShell` (relevant
  inside any entry that needs to vary behavior per runtime).
