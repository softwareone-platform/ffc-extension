# Modal conventions

The app ships as a single standalone bundle, so every modal is an **in-app
modal**: rendered inside the React tree, its open/close state driven by
`useModalToggle()`. There is no host-mounted / separate-bundle modal shape.

Two flavours exist:

- **Simple form modals** — a `Create<Entity>StandaloneModal` that wraps
  `<StandaloneModal>` around a form.
- **Wizard modals** (multi-step) — a single component that renders
  `@swo/design-system/wizard`'s `<Wizard>` inside a modal. Entitlement
  creation is the current example.

## State: `useModalToggle`

`useModalToggle({ onSuccess })` (`src/shared/hooks/useModalToggle.ts`) owns the
open/close boolean and optional payload:

```tsx
const addUserModal = useModalToggle({ onSuccess: refresh });

<Button onClick={addUserModal.open}>Add user</Button>
<CreateUserStandaloneModal
  isOpen={addUserModal.isOpen}
  onClose={addUserModal.close}
/>
```

`close(result?)` takes a `ModalCloseResult` — `onSuccess` fires **only** when
the modal closes with `{ success: true }`.

## The close contract

Types live in `src/shared/components/modal/types.ts`:

```ts
type ModalCloseResult = { success?: boolean };
type ModalControllerProps = { onClose?: (result?: ModalCloseResult) => void };
```

A modal calls `onClose({ success: true })` on a successful submit and
`onClose()` on cancel.

## Simple form modals

The modal wraps `<StandaloneModal>` (`src/shared/components/modal/StandaloneModal.tsx`),
which renders `@swo/design-system/modal`'s `<Modal>` with our common defaults
(width, cancel/submit actions via `ModalCancelButton`). Form logic lives in a
shared `use<Entity>FormController` hook so the modal component stays thin.

```tsx
export function CreateUserStandaloneModal({ isOpen, onClose, className }: Props) {
  const { control, error, isPending, submit, handleCancel } =
    useUserFormController({ onClose });

  return (
    <StandaloneModal
      isOpen={isOpen}
      onClose={onClose}
      onCancel={handleCancel}
      onSubmit={() => submit()}
      isSubmitting={isPending}
    >
      <form onSubmit={submit}>
        <UserFormFields control={control} error={error} />
      </form>
    </StandaloneModal>
  );
}
```

## Wizard modals (multi-step)

Multi-step create flows are a single component under `<flow>-wizard/` that
renders `<Wizard>` inside `@swo/design-system/modal`'s `<Modal>` and owns its
`react-hook-form` + `react-query` mutation across steps — there is **no**
`use<Entity>FormController`. Entitlement creation
(`features/entitlements/create-entitlement-wizard/`) is the example:

- `CreateEntitlementWizard.tsx` — the modal component. Props `{ isOpen, onClose }`;
  calls `onClose({ success: entitlementCreated })`.
- `steps/` — one component per wizard step.
- `useSteps.tsx`, `CreateEntitlement.Schema.tsx` — step config and zod schema.

Same `ModalCloseResult` contract, so `useModalToggle`'s `onSuccess` still fires
on a successful create.

## Shared form controller

> Applies to **simple form modals** only. Wizard modals manage their own form
> state across steps and do not use a form controller.

`use<Entity>FormController({ onClose })` owns:

- `react-hook-form` setup (`useAdd<Entity>Form`, schema in
  `Add<Entity>Form.Schema.tsx`).
- the `react-query` mutation (calls the right API client method).
- `handleCancel` / `submit` / `onSuccess` / `onError` plumbing — all routed
  through the supplied `onClose`.

## File layout per feature

Modal code lives next to the feature it belongs to (not in a separate
`features/modal/` tree), nested under the parent resource when applicable
(e.g. user modals under `organizations/details/users/`).

Simple form modal:

```
features/<feature>/modal/
├── Add<Thing>Form.Schema.tsx        # zod schema + types
├── <Thing>FormFields.tsx            # the actual <input>s
├── Create<Thing>StandaloneModal.tsx # the modal component
└── hooks/
    ├── useAdd<Thing>Form.tsx        # react-hook-form wrapper
    └── use<Thing>FormController.ts  # mutation + onClose plumbing
```

Wizard modal:

```
features/<feature>/<flow>-wizard/
├── Create<Thing>Wizard.tsx     # the modal component (Wizard inside Modal)
├── Create<Thing>.Schema.tsx    # zod schema + types
├── steps/                      # one component per step
└── useSteps.tsx
```

## Shared modal pieces

In `frontend/src/shared/`:

- `shared/components/modal/StandaloneModal.tsx` — the `<Modal>` wrapper.
  Forwards the design-system props and provides default cancel/submit actions
  if `actions` isn't passed.
- `shared/components/modal/ModalCancelButton.tsx` — the cancel button variant.
- `shared/components/modal/types.ts` — the `ModalCloseResult` /
  `ModalControllerProps` types.
- `shared/hooks/useModalToggle.ts` — open/close state hook with an
  `onSuccess` callback.

## Adding a new modal

For a single-step **simple form modal**:

1. Create `Add<Entity>Form.Schema.tsx` with a `zod` schema + inferred type.
2. Create `<Entity>FormFields.tsx` — the inputs, controlled via
   `react-hook-form`'s `control` prop.
3. Create `hooks/useAdd<Entity>Form.tsx` — `useForm()` wrapper with
   `zodResolver`.
4. Create `hooks/use<Entity>FormController.ts` — mutation + cancel + close
   plumbing. Take `{ onClose }`.
5. Create `Create<Entity>StandaloneModal.tsx` wrapping `<StandaloneModal>`.
6. Render it in the feature, gated by a `useModalToggle()` boolean.

For a **multi-step** flow, build a wizard instead (see
[Wizard modals](#wizard-modals-multi-step)).

## See also

- [MPT host integration](../architecture/mpt-host-integration.md) — the app
  can run inside the MPT host iframe; `useNotifyParentChildModal` tells the
  host when a modal is open.
- [API hook conventions](./api-hooks.md) — the controllers consume
  `useFooApi()` for mutations.
