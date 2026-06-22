# Frontend file & folder naming convention

This project mirrors the naming convention used by `@swo/*` packages
(see `frontend/node_modules/@swo/<package>`). When adding or refactoring
files under `frontend/src`, follow the rules below.

## Rules

1. **Folders (directories): `kebab-case`.**
   - Examples (from `@swo`): `auth-react/`, `date-picker/`, `mp-status-chip/`, `design-system/`.
   - In `src`: `entries/`, `features/organizations/`, `details/data-sources/`, `shared/components/page-shell/`.
   - Internal multi-word folders inside a package (e.g. `@swo/auth-react/lib/errorHandler`) are rare;
     prefer `kebab-case` for consistency.

2. **Component / class / type-like files: `PascalCase` + `.tsx`/`.ts`.**
   - The file name matches the primary export.
   - Examples (from `@swo`): `Button.d.ts`, `Modal.d.ts`, `ConfirmModal.d.ts`,
     `Modal.Header.d.ts`, `DatePicker.Calendar.MonthView-*.mjs`,
     `Grid.Toolbar.Shared.ButtonLink-*.mjs`.
   - In `src`: `MainLayout.tsx`, `PageShell.tsx`,
     `EntityStatusChip.tsx`, `ExtensionsProvider.tsx`, `MPTContextProvider.tsx`,
     `OrganizationsGrid.tsx`, `DetailsLayout.tsx`, `EntitlementsGrid.tsx`,
     `EntitlementsForm.tsx`, `Users.tsx`, `DataSources.tsx`.

3. **Hooks: `camelCase` starting with `use…` + `.ts`/`.tsx`.**
   - Examples (from `@swo/modal/lib/hooks`): `useConfirm.d.ts`, `useConfirmModal.d.ts`,
     `useConfirmWithReason.d.ts`, `useModal.d.ts`.
   - In `src`: `useFixedT.ts`, `useReactQueryRqlGrid.ts`, `useAsyncOptions.ts`,
     `useColumns.tsx`, `useFields.tsx`, `useViews.tsx`,
     `useOrganizationsApi.tsx`, `useOrganizationDetailsApi.ts`.

4. **Companion / sibling files use a `.` qualifier on the same PascalCase base.**
   - Examples (from `@swo`): `Modal.Header.d.ts`, `Modal.Left.d.ts`,
     `index.d.ts`, `package.json`.
   - In `src`: `OrganizationsGrid.tsx` + `OrganizationsGrid.config.tsx`,
     `DataSourcesGrid.tsx` + `DataSourcesGrid.config.tsx`,
     `UsersGrid.tsx` + `UsersGrid.config.tsx`,
     `DetailsLayout.tsx` + `DetailsLayout.scss`,
     `EntryModalWidget.tsx` + `EntryModalWidget.scss`.

5. **SCSS files for a component share the component's PascalCase base name**
   (`Component.scss`), imported relatively (`import './Component.scss'`).

6. **Tests / specs append `.spec.tsx` / `.spec.ts`** preserving the base name:
   `useReactQueryRqlGrid.spec.tsx`.

7. **Barrel files stay `index.ts`** and only re-export from the renamed PascalCase files:
   ```ts
   export { PageShell } from './PageShell';
   ```

8. **TS path aliases (`~app`, `~features`, `~shared`, `~i18n`,
   `~organizations`)** in `tsconfig.json` and `esbuild.config.js` point at
   `kebab-case` folders. Only the file suffix changes — folder paths remain
   `kebab-case`:
   ```ts
   import { PageShell } from '~shared/components/page-shell';      // folder
   import { useFixedT } from '~shared/hooks/useFixedT';            // file
   import { OrganizationsGrid } from '~features/organizations/list/OrganizationsGrid';
   ```

## Translation keys

Translation keys in `frontend/src/i18n/*.json` follow their own naming
rules. The short version:

- **Path separator is `:`**, not `.` (i18next is configured with
  `keySeparator: ":"`).
- **Top-level grouping:** `<feature>:*` (e.g. `organization:*`,
  `entitlement:*`) for feature-owned strings, `shared:*` for cross-feature
  groups (`shared:nav`, `shared:grid:columns`, `shared:properties`, …).
- **Leaf casing follows intent, not casing dogma:**
  - `snake_case` when the key mirrors an API field name
    (`affiliate_external_id`, `parent_id`, `data_source`, `display_name`,
    `azure_cnr`) — so dynamic lookups like `tProperties(field)` work
    without conversion.
  - `camelCase` for UI-only labels (`lastLogin`, `createdAt`,
    `billingCurrency`, `forecastThisMonth`).
  - `snake_case` for compound action verbs (`add_user`, `add_entitlement`,
    `create_failed`).

Don't translate snake_case API fields into camelCase keys — that breaks
dynamic-lookup sites. Full conventions, dynamic-key patterns, and the
"add a locale" recipe live in
[`./i18n.md`](./i18n.md).

## Applying the convention

1. Rename with `git mv` so history is preserved. On case-insensitive filesystems (macOS default), case-only renames may need a two-step via a temp name to avoid `TS1149` / `TS1261`.
2. Update every import — including barrels (`index.ts`), dynamic `import('…')`, SCSS imports, and `*.spec.tsx`.
3. Verify with `cd frontend && npx tsc --noEmit`. Restart the editor's TS server if stale errors persist after a case-only rename.

**Do not rename**: `index.ts`, `package.json`, `tsconfig*.json`, `esbuild.config.js`, `eslint.config.mjs`, `global.d.ts`, locale JSON files (`en.json`, `<lang>.json`), or anything inside `node_modules/`.
