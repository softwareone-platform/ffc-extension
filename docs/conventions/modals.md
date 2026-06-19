# Modal conventions

Every "create / edit" modal in this app ships in **two** shapes that share
their form logic. Pick the right one for the call site; if you find
yourself writing only one of them, you're probably missing the other.

## The two shapes

### `<Entity>EntryModal` — host-mounted, separate bundle

Used when the MPT host opens the modal by id via the SDK
(`useMPTModal().open("finops.admin.create-user-modal", { … })`). The modal
lives in its own esbuild bundle under `frontend/src/entries/Create<Entity>Modal.tsx`
and is wired in by `mountModalEntry(<EntryModal />)`. The host supplies the
`onClose` prop.

- Component type: `ModalEntryComponent` (`src/shared/components/modal/modalEntry.ts`):
  ```ts
  type ModalEntryProps = { onClose?: (result?: ModalCloseResult) => void };
  type ModalEntryComponent = ComponentType<ModalEntryProps>;
  type ModalCloseResult = { success?: boolean };
  ```
- Rendering: wraps content in `<EntryModalWidget title=…>` — *host chrome,
  no `<Modal>`* (the host already provides the modal frame).
- The modal calls `onClose({ success: true })` on successful submit,
  `onClose()` or `close("cancel")` on cancel.

### `<Entity>StandaloneModal` — in-app, React state

Used when the app itself opens the modal (in standalone-shell mode where
the MPT host modal API isn't available). The modal is rendered conditionally
inside a component tree based on a `useModalToggle()` boolean, and uses the
`<StandaloneModal>` wrapper (`src/shared/components/modal/StandaloneModal.tsx`)
which renders `@swo/design-system/modal`'s `<Modal>` with our common defaults.

- Props: `{ isOpen, onClose, … }`. Same `ModalCloseResult` contract for
  `onClose`.
- Use `useModalToggle({ onSuccess })` (`src/shared/hooks/useModalToggle.ts`)
  to manage the open/close state — it calls `onSuccess` only when the modal
  closes with `{ success: true }`.

## Picking which to render

Use `useIsStandaloneShell()` (see [`standalone-mode.md`](../architecture/standalone-mode.md)):

```tsx
const isStandaloneShell = useIsStandaloneShell();
const addUserModal = useModalToggle({ onSuccess: refresh });

return (
  <>
    {isStandaloneShell ? (
      <Button onClick={addUserModal.open}>Add user</Button>
    ) : (
      <Button onClick={() => mpt.open("finops.admin.create-user-modal", { … })}>
        Add user
      </Button>
    )}

    {isStandaloneShell && (
      <CreateUserStandaloneModal
        isOpen={addUserModal.isOpen}
        onClose={addUserModal.close}
      />
    )}
  </>
);
```

The MPT host knows about `EntryModal`s via its modal registry; the in-app
`StandaloneModal` lives entirely in our tree.

## Shared form controller

Both shapes consume the same `use<Entity>FormController({ onClose })` hook,
which owns:

- `react-hook-form` setup (`useAdd<Entity>Form`, schema in
  `Add<Entity>Form.Schema.tsx`).
- `react-query` mutation (calls the right API client method).
- `handleCancel` / `handleSubmit` / `onSuccess` / `onError` plumbing — calls
  the supplied `onClose` *or* falls back to the SDK's `close("cancel")` /
  `close({ success: true })` so it works in both entry and standalone modes.

```ts
// inside both Entry and Standalone modals:
const { control, error, isPending, submit, handleCancel } =
  useUserFormController({ onClose });
```

If you find yourself implementing two different form controllers for one
modal pair, consolidate them — the entry and standalone wrappers must
behave identically.

## File layout per feature

After the modal reorganisation, modal code lives **next to the feature it
belongs to**, not in a separate `features/modal/` tree.

```
features/entitlements/modal/
├── AddEntitlementForm.Schema.tsx   # zod schema + types
├── EntitlementsFormFields.tsx      # the actual <input>s
├── CreateEntitlementEntryModal.tsx     # host-mounted shape
├── CreateEntitlementStandaloneModal.tsx # in-app shape
└── hooks/
    ├── useAddEntitlementForm.tsx   # react-hook-form wrapper
    └── useEntitlementFormController.ts  # mutation + onClose plumbing

features/organizations/details/users/modal/
├── AddUserForm.Schema.tsx
├── UserFormFields.tsx
├── CreateUserEntryModal.tsx
├── CreateUserStandaloneModal.tsx
└── hooks/
    ├── useAddUserForm.tsx
    └── useUserFormController.ts
```

User modals nest under `organizations/details/users/` because Users are a
sub-resource of Organizations in this app (not a top-level feature).

## Shared modal pieces

In `frontend/src/shared/`:

- `shared/components/modal/StandaloneModal.tsx` — the in-app `<Modal>`
  wrapper. Forwards all the design-system props and provides default
  cancel/submit actions if `actions` isn't passed.
- `shared/components/modal/EntryModalWidget.tsx` + `.scss` — the host-modal
  layout primitive (title + body, no chrome).
- `shared/components/modal/ModalCancelButton.tsx` — the cancel button
  variant used in both shapes.
- `shared/components/modal/modalEntry.ts` — the `ModalEntryComponent` /
  `ModalEntryProps` / `ModalCloseResult` types.
- `shared/hooks/useModalToggle.ts` — open/close state hook with
  `onSuccess` callback.

## Adding a new modal

1. Create `Add<Entity>Form.Schema.tsx` with a `zod` schema + inferred type.
2. Create `<Entity>FormFields.tsx` — the actual inputs, controlled via
   `react-hook-form`'s `control` prop.
3. Create `hooks/useAdd<Entity>Form.tsx` — `useForm()` wrapper with
   `zodResolver`.
4. Create `hooks/use<Entity>FormController.ts` — mutation + cancel + close
   plumbing. Accept `onClose?: ModalEntryProps["onClose"]`.
5. Create `Create<Entity>StandaloneModal.tsx` (in-app shape) and
   `Create<Entity>EntryModal.tsx` (host shape) using both. **Don't skip the
   pair** — they always go together.
6. Add an `entries/Create<Entity>Modal.tsx` calling
   `mountModalEntry(<Create<Entity>EntryModal />)`, then add that file to
   `frontend/esbuild.config.js`'s `entryPoints`.
7. Register the entry id with the host's modal registry.

## See also

- [Entry modes](../architecture/entry-mode.md) — `mountModalEntry` and the
  other entry shapes.
- [Standalone mode flags](../architecture/standalone-mode.md) — why
  `useIsStandaloneShell` is the right gate for picking entry vs standalone.
- [API hook conventions](./api-hooks.md) — the controllers consume
  `useFooApi()` for mutations.
