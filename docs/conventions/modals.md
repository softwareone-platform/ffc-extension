# Modal conventions

Modals in this app come in two flavours:

- **Simple form modals** ship in **two shapes** that share their form logic —
  an `<Entity>EntryModal` (host-mounted) and an `<Entity>StandaloneModal`
  (in-app). Pick the right one for the call site; if you find yourself writing
  only one of them, you're probably missing the other.
- **Wizard modals** (multi-step) ship as a **single shared body** mounted in
  both modes. See [Wizard modals](#wizard-modals-multi-step) below — entitlement
  creation is the current example.

## The two shapes (simple form modals)

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

## Wizard modals (multi-step)

Multi-step create flows don't fit the two-shape form pair — instead a **single
shared wizard body** is mounted in both modes. Entitlement creation is the
current example (`features/entitlements/create-entitlement-wizard/`):

- **Body**: `CreateEntitlement.tsx` (default export, imported as
  `EntitlementWizard`). It renders `@swo/design-system/wizard`'s `<Wizard>`
  with its own header/steps/actions, and owns its `react-hook-form` +
  `react-query` mutation across steps — there is **no** `use<Entity>FormController`.
- **Host-mounted**: `entries/CreateEntitlementModal.tsx` does
  `mountModalEntry(<EntitlementWizard />)`. No `EntryModalWidget` wrapper — the
  wizard is the whole modal body and the host provides the frame.
- **In-app**: `CreateEntitlementWizard.tsx` wraps the body in
  `<StandaloneModal isFullScreen isToHidePadding>` (no title/footer — the wizard
  supplies its own).

Close plumbing is built into the body via an optional prop:

```ts
type Props = { onClose?: (result?: ModalCloseResult) => void };
```

- **Standalone** passes `onClose`; the wizard calls it with
  `{ success: entitlementCreated }`.
- **Embedded** omits it; the wizard falls back to `useMPTModal().close({ entitlementCreated })`.

Same `ModalCloseResult` contract as the form modals, so `useModalToggle`'s
`onSuccess` still fires on a successful create.

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
      <Button onClick={() => mpt.open("finops.admin.create-user-modal", )}>
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

> Applies to the **simple form modal** pair only. Wizard modals (above) manage
> their own form state across steps and do not use a form controller.

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

Modal code lives next to the feature it belongs to (not in a separate `features/modal/` tree), and nests under the parent resource when applicable (e.g. user modals under `organizations/details/users/`).

Simple form modals:

```
features/<feature>/modal/
├── Add<Thing>Form.Schema.tsx       # zod schema + types
├── <Thing>FormFields.tsx           # the actual <input>s
├── Create<Thing>EntryModal.tsx     # host-mounted shape
├── Create<Thing>StandaloneModal.tsx # in-app shape
└── hooks/
    ├── useAdd<Thing>Form.tsx       # react-hook-form wrapper
    └── use<Thing>FormController.ts # mutation + onClose plumbing
```

Wizard modals (see [Wizard modals](#wizard-modals-multi-step)):

```
features/<feature>/<flow>-wizard/
├── Create<Thing>.tsx                       # shared wizard body (default export)
├── Create<Thing>WizardStandaloneModal.tsx  # in-app wrapper (<StandaloneModal>)
├── steps/                                  # one component per step
└── useSteps.tsx
```

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

> For a **multi-step** flow, skip the form pair below and build a wizard instead
> (see [Wizard modals](#wizard-modals-multi-step)): one shared body mounted by
> `mountModalEntry` for the host and wrapped in `<StandaloneModal>` for in-app,
> with an optional `onClose` prop for the standalone case.

For a single-step **simple form modal**:

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
