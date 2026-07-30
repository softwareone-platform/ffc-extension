# Entry modes

This frontend ships as **multiple independent bundles**, not one SPA. Sources
live under `frontend/src/entries/`, grouped by shape:

- `standalone/` — full-SPA entries (e.g. `SandboxStandaloneRoot.tsx`).
- `single-entry/` — per-feature entries (`OrganizationsEntry.tsx`, `EntitlementsEntry.tsx`).
- `modals/` — host-mounted modal entries (`CreateEntitlementModal.tsx`).

`frontend/esbuild.config.js` lists each as an `{ in, out }` pair. `out` is a
**flat** bundle name, so grouping sources into subfolders still emits the files
at `../static/<Name>.js` — the paths the MPT host and `meta.yaml` reference. The
host loads whichever bundle it needs, when it needs it.

Three entry shapes are in use, one helper per shape. All live in
`frontend/src/app/bootstrap/` and go through the same `mount()` function, which
delegates to `@mpt-extension/sdk`'s `setup()` so the host controls where the
React root attaches.

## Shapes

### 1. Standalone entry — `mountStandaloneEntry(router)`

Mounts the **full SPA** via React Router's `RouterProvider`. One bundle, all routes.

```tsx
// frontend/src/entries/standalone/SandboxStandaloneRoot.tsx
const router = createBrowserRouter([/* ... */]);
mountStandaloneEntry(router);
```

### 2. Feature ("single") entry — `mountFeatureEntry(routes)`

Mounts a **single feature's routes** inside a `BrowserRouter` + `Routes`. One
bundle per feature, loaded by the host when that section is opened.

```tsx
// frontend/src/entries/single-entry/EntitlementsEntry.tsx
mountFeatureEntry(
  <>
    <Route index element={<EntitlementsGrid />} />
    <Route path={SEGMENTS.idParam} element={<DetailsLayout … />}>
      …
    </Route>
  </>,
);
```

In use: `single-entry/OrganizationsEntry.tsx`, `single-entry/EntitlementsEntry.tsx`.

### 3. Modal entry — `mountModalEntry(<Modal />)`

Mounts a **single modal component** (no router). The host opens these by id
through the MPT SDK (e.g. `open("finops.admin.create-entitlement-modal", { … })`)
and they render in place inside the host chrome.

```tsx
// frontend/src/entries/modals/CreateEntitlementModal.tsx
import EntitlementWizard from "~features/entitlements/create-entitlement-wizard/CreateEntitlement";

mountModalEntry(<EntitlementWizard />);
```

Modal components implement `ModalEntryComponent` (`shared/components/modal/modalEntry.ts`):

```tsx
type ModalCloseResult = { success?: boolean };
type ModalEntryProps = { onClose?: (result?: ModalCloseResult) => void };
type ModalEntryComponent = ComponentType<ModalEntryProps>;
```

The host supplies `onClose`; the modal calls it with `{ success: true }` on
successful submit, or with no argument on cancel.

## Provider stack

`mount()` wraps whatever tree an entry passes in `ExtensionsProvider` (i18n +
React Query + MPT context) before rendering, so every entry gets the same
context without repeating it. Standalone and feature entries pass a router as
that tree; modal entries pass the modal directly.

```
mount(node)                       // SDK setup → wraps node → createRoot.render
  └─ ExtensionsProvider           // i18n + React Query + MPT context
       └─ <entry-specific tree>   // router (standalone / feature) or modal
```

## Adding a new entry

1. Decide the shape: standalone / feature / modal.
2. Create the file under the matching `src/entries/<shape>/` folder and call the
   appropriate `mount*Entry(...)` helper.
3. Add an `{ in, out }` pair to `entryPoints` in `frontend/esbuild.config.js`
   (`out` = the flat bundle name emitted to `../static/`).
4. For modal entries: the modal component lives next to its owning feature
   (e.g. `features/entitlements/modal/`), and the host references the bundle by
   id in `meta.yaml`. See [`docs/conventions/modals.md`](../conventions/modals.md).

## See also

- [MPT host integration](./mpt-host-integration.md) — how the host bridge
  works inside any entry that runs embedded.
- [Standalone mode flags](./standalone-mode.md) — disambiguating
  `useHasMPTHost` / `useIsRootPage` / `useIsStandaloneShell` (relevant inside
  any entry that needs to vary behavior per runtime).
