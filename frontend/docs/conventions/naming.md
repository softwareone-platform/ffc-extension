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
   - In `src`: `AppShell.tsx`, `MainLayout.tsx`, `PageShell.tsx`,
     `EntityStatusChip.tsx`, `ExtensionsProvider.tsx`, `MPTContextProvider.tsx`,
     `OrganizationsGrid.tsx`, `DetailsLayout.tsx`, `EntitlementsGrid.tsx`,
     `AddOrganizationModal.tsx`, `Users.tsx`, `DataSources.tsx`.

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
     `ModalWidget.tsx` + `ModalWidget.scss`.

5. **SCSS files for a component share the component's PascalCase base name**
   (`Component.scss`), imported relatively (`import './Component.scss'`).

6. **Tests / specs append `.spec.tsx` / `.spec.ts`** preserving the base name:
   `useReactQueryRqlGrid.spec.tsx`.

7. **Barrel files stay `index.ts`** and only re-export from the renamed PascalCase files:
   ```ts
   export { PageShell } from './PageShell';
   ```

8. **TS path aliases (`~app`, `~features`, `~shared`, `~i18n`, `~styles`,
   `~organizations`)** in `tsconfig.json` and `esbuild.config.js` point at
   `kebab-case` folders. Only the file suffix changes — folder paths remain
   `kebab-case`:
   ```ts
   import { PageShell } from '~shared/components/page-shell';      // folder
   import { useFixedT } from '~shared/hooks/useFixedT';            // file
   import { OrganizationsGrid } from '~features/organizations/list/OrganizationsGrid';
   ```

## How to apply the convention (step-by-step for an AI agent)

When asked to "apply the `@swo` naming convention" to a folder:

1. **Survey the reference**: list a few `frontend/node_modules/@swo/*` packages
   and their `lib/` contents to confirm the casing rules above are still in
   effect.
2. **Inventory the target folder** (`frontend/src/...`) and classify each file:
   - React component / class / context provider / layout → `PascalCase`.
   - Hook (export starts with `use…`) → `camelCase` starting with `use`.
   - Config / styles / spec sibling → keep the sibling's PascalCase base and
     add a `.config`, `.scss`, `.spec` qualifier.
   - Folders → leave as `kebab-case` (rename to `kebab-case` if not already).
3. **Rename with `git mv`** so history is preserved:
   ```sh
   git mv frontend/src/path/old-name.tsx frontend/src/path/NewName.tsx
   ```
   On case-insensitive filesystems (macOS default) git mv handles case-only
   renames, but if TypeScript complains about duplicate filenames differing
   only in casing, perform a two-step rename through a temporary name:
   ```sh
   git mv -f path/Foo.tsx path/Foo_tmp.tsx
   git mv -f path/Foo_tmp.tsx path/Foo.tsx
   ```
4. **Update every import** that referenced the old path. Search patterns:
   ```sh
   grep -rnE "from ['\"][~\.][^'\"]*(old-kebab-name)" frontend/src
   grep -rnE "import\\(['\"][~\.][^'\"]*(old-kebab-name)" frontend/src
   ```
   Don't forget:
   - barrel files (`index.ts`),
   - dynamic `import('…')` calls in `frontend/src/app/router.tsx`,
   - SCSS imports (`import './foo.scss'`),
   - test files (`*.spec.tsx`).
5. **Verify**:
   ```sh
   cd frontend && npx tsc --noEmit
   ```
   The TypeScript language server in editors may keep a stale cache after
   case-only renames — restart the TS server / editor if `tsc` is clean but
   the editor still reports `TS1149` / `TS1261`.
6. **Do not rename** `index.ts`, `package.json`, `tsconfig*.json`,
   `esbuild.config.js`, `eslint.config.mjs`, `global.d.ts`, JSON locale files
   (`en.json`, `en_US.json`) or anything inside `node_modules/`.
