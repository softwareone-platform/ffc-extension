# Sandbox Standalone

This feature is a standalone sandbox shell for extension UI exploration.

## Structure

- `manifest.ts` is the single source of truth for sandbox sections.
  - Top-level sections drive route generation in `routes.tsx`.
  - The same section data drives side navigation in `navigation.config.ts`.
  - News sub-sections drive header tabs in `pages/news/NewsPage.tsx`.
- `StandaloneLayout.tsx` provides shell chrome only.
- `components/SandboxHeaderActions.tsx` hosts sandbox-specific header actions.

## Modal approach

Sandbox modals use plain `@swo/design-system/modal` directly (`CreateUserModal`,
`ConsentModal`) to keep the implementation simple and explicit.

## Consent persistence behavior

`ConsentModal` stores consent in `localStorage` under
`sandboxStandalone.consent.v1` when storage is available.

When rendered in restricted sandboxed iframes (for example without
`allow-same-origin`), browser storage access can throw. In that case, the modal
falls back to in-memory behavior for the current session and does not persist
across reloads.

