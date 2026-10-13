---
name: ffc-extension
description: Project-specific bindings for ffc-extension (the local MPT project). Resolves concrete values the mpt-* skills reference abstractly — alias names, CSS prefix, shared wrapper paths, shared hook names, test-utils inventory, entity list, i18n namespaces, SCSS class list, project scripts. Use whenever any frontend task touches ffc-extension — in combination with mpt-frontend-standards, mpt-design-system, mpt-poc-builder, or mpt-module-testing. In another MPT project this file is replaced by that project's own project bindings skill with its own bindings.
---

# ffc-extension project bindings

The `mpt-*` skills are written to be portable across MPT frontend projects.
When they reference "the project's shared panel wrapper" or "the project's
test-utils factories", resolve those names using the table below.

In another MPT project this file is replaced by that project's own skill
(typically named after the repo) with its own bindings.

## TS path aliases

Configured in [`frontend/tsconfig.json`](../../../frontend/tsconfig.json) +
[`frontend/jest.config.js`](../../../frontend/jest.config.js) (both must stay
in sync — the TS resolver and Jest's `moduleNameMapper` are separate).
**Always import by alias — never climb `../../../`.**

Complete inventory (9 aliases):

| Alias              | Points at                                 | Use for                                                                       |
| ------------------ | ----------------------------------------- | ----------------------------------------------------------------------------- |
| `~app/*`           | `frontend/src/app/*`                      | App shell: router, root providers, bootstrap wiring                           |
| `~api/*`           | `frontend/src/api/*`                      | Generated / shared API types (`ffc-api-model`)                                |
| `~shared/*`        | `frontend/src/shared/*`                   | Hooks, utils, UI primitives, styles, mock helpers reused across features      |
| `~features/*`      | `frontend/src/features/*`                 | Cross-feature references (e.g. `~features/organizations/paths`)               |
| `~organizations/*` | `frontend/src/features/organizations/*`   | Deep links into the organizations feature from outside its folder             |
| `~entitlements/*`  | `frontend/src/features/entitlements/*`    | Deep links into the entitlements feature from outside its folder              |
| `~i18n/*`          | `frontend/src/i18n/*`                     | Translation resources + the `sortTranslations` script module                  |
| `~fixes/*`         | `frontend/src/fixes/*`                    | Local vendor patches / monkey-patches waiting on upstream fixes               |
| `~test-utils`, `~test-utils/*` | `frontend/src/test-utils[/<path>]` | Render wrappers, factories, shared jest mocks — **spec files only** |

Rule of thumb: use the **narrowest** alias that fits — prefer `~organizations/...` over `~features/organizations/...` when you're reaching into that feature from another.

## CSS prefix

**No shared `.ffc-*` layer currently ships** at `~shared/styles/_components.scss`.
Features use CSS Modules (`<Component>.module.scss` siblings) for
per-component styling. See [`docs/conventions/design-system.md`](../../../docs/conventions/design-system.md#component-styling)
for the current pattern.

The `.ffc-*` prefix is **reserved** for the future shared layout layer. The
planned class vocabulary (based on dashboard POC experimentation on
`sandbox/dashboard`):

- **Tab + panel layout:** `.ffc-tab-stack`, `.ffc-panel-grid`, `.ffc-panel`,
  `.ffc-panel--full`, `.ffc-panel--span-4`, `.ffc-panel--span-8`
- **KPI rows:** `.ffc-kpi-row`, `.ffc-kpi-row--four`, `.ffc-kpi-row--quad`,
  `.ffc-kpi-row--column`
- **Chart composition:** `.ffc-chart-split`, `.ffc-chart-split--triple`, `.ffc-legend`
- **Filter affordances:** `.ffc-filter-bar`, `.ffc-multiselect`

Update this section (and promote to the "shipped" state) when the shared
layer actually lands.

## Shared wrappers (`~shared/components/*`)

Currently shipped:

| Area                | Import from                                | Public exports                                                          |
| ------------------- | ------------------------------------------ | ----------------------------------------------------------------------- |
| Modal               | `~shared/components/modal/Modal`           | `Modal`; cancel action from `~shared/components/modal/ModalCancelButton` |
| Entity events / timestamps | `~shared/components/events` / `~shared/components/timestamps` | `EntityEvents`, `EventTimestamps` |
| CardSection         | `~shared/components/CardSection`           | `CardSection` (layout wrapper around DS Card)                            |
| EntityProperties    | `~shared/components/EntityProperties`      | `EntityProperties` (two-column property list)                            |

**Planned but not yet in the tree** (recipes in [`docs/conventions/design-system-components.md`](../../../docs/conventions/design-system-components.md) describe target shape — add the wrapper in the first PR that needs it):

- `~shared/components/panel` — `Panel`, `KpiTile`, `KpiTileProps`
- `~shared/components/charts` — `XyChart`, `DonutChart`, `ChartLegend`, palette constants, shared series type

## Shared hooks (`~shared/hooks/*`)

| Hook                           | Purpose                                                             |
| ------------------------------ | ------------------------------------------------------------------- |
| `useFixedT(prefix)`            | i18n wrapper around `useTranslation` with a fixed key prefix        |
| `useFormatDate()`              | Locale-aware date formatter for grid cells                           |
| `useModalToggle({ onSuccess })` | In-app modal open/close state with a success callback               |

## Shared utils (`~shared/utils/*`)

Current inventory (grep `frontend/src/shared/utils/` for the full list):

| Util                                           | Purpose                                                           |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| `mapAxiosResponseDataList` (`ListResponse<T>`) | Shared list-response envelope type (`items?: T[]`)                |
| `rqlHelper` (`getCustomQueryString`)           | Builds RQL query strings for grid list endpoints                  |
| `DateUtils`, `NumberUtils`                     | Locale-aware primitives for cells / summaries                     |
| `lazyComponent`                                | React.lazy helper with dynamic-import handling                    |

**POCs needing an axios-shaped mock promise should add their own helper** — the project does not ship a shared `mockResponse` util yet. If one is added, document it here. The helper only needs to return a `Promise<AxiosResponse<T>>` with a configurable delay so react-query components exercise their loading states.

## Test-utils inventory (`~test-utils/*`)

| Area              | Exports                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------- |
| Render wrappers   | `renderWithRouter`, `renderWithEntitlementRoute`, `renderWithOrganizationRoute`, `createQueryClientWrapper` |
| Grid helpers      | `renderCell(column, item)`, `columnByName(columns, name)`                                     |
| Modal helpers     | `triggerModalSubmit(mockModal)`, `triggerModalCancel(mockModal)`                              |
| Factories         | `makeAccount`, `makeDatasource`, `makeEmployee`, `makeEntitlement`, `makeOrganization`        |
| Shared jest mocks | `~test-utils/mocks/<name>` — see "Shared mock modules" below                                  |

### Shared mock modules (`~test-utils/mocks/*`)

One mock per file. Browse `frontend/src/test-utils/mocks/` for the full list.
Current inventory (names stable):

```
controlledInput        designSystemButton       designSystemGrid         designSystemNavigation
designSystemNotification designSystemSkeleton    designSystemText         designSystemUtils
entityReferenceCell    errorDetails             fixedT                   gridCellCurrency
gridCellDate           gridCellDynamicActions   gridHooks                inPageHighlight
inlineErrorNotification modal                   notifyParentChildModal   routeGuard
userRole               wizardStep               customIcon
```

Each file exports both a **spy** (`mockUseX`) and a **module shape**
(`mockXModule`), wired to call the spy.

## Entities + feature folders

Features live in `frontend/src/features/<entity>/`. Current list:

- `organizations/` — organization CRUD + details (users, data sources, events). Dedicated alias: **`~organizations/*`**.
- `entitlements/` — entitlement list, details, create wizard. Dedicated alias: **`~entitlements/*`**.

**Use the dedicated entity alias when you have one** (`~organizations/paths`, `~entitlements/api`) — it's narrower and makes the dependency obvious to readers. Fall back to `~features/<entity>/...` only when a dedicated alias doesn't exist.

Entity grid route helpers:

- `renderWithEntitlementRoute(ui, { id, routePath })`
- `renderWithOrganizationRoute(ui, { id, routePath })`

Entity factories (typed `Partial<T>` builders):

- `makeOrganization`, `makeEntitlement`, `makeEmployee`, `makeDatasource`, `makeAccount`

## i18n

- **Hook:** `useFixedT(prefix)` from `~shared/hooks/useFixedT`
- **Resource file:** `frontend/src/i18n/en.json`
- **Top-level namespaces in `en.json`:** `organization`, `organizations`, `entitlement`, `entitlements`, `shared`, `errorPage`. The singular form (`organization`, `entitlement`) holds detail-page strings; the plural (`organizations`, `entitlements`) holds list / grid / wizard actions. `shared` is cross-feature; `errorPage` is the root error-boundary strings.
- **Key separator:** `:` (not `.`)
- **Sort script:** `npm run translations:sort` (also runs via the project's
  `i18n/sortTranslations.ts`)

## Verification commands

```bash
cd frontend
npx tsc --noEmit                    # type-check
npm run build                       # catches SCSS token errors tsc misses
npx prettier --write <touched files>
npx eslint <touched files>
npm test                            # jest + tsc + prettier + eslint in parallel
```

## MPT host integration

- `useHasMPTHost()` — detects the iframe host runtime
- `useIsRootPage()` — distinct from `useHasMPTHost`; see
  [`docs/architecture/mpt-host.md`](../../../docs/architecture/mpt-host.md)
- `useNotifyParentChildModal()` — tells the host when an in-app modal opens

## Where humans edit these values

Convention docs live in [`docs/conventions/`](../../../docs/conventions/) and
describe the same bindings from a human-facing angle. Those docs are the
project's canonical source — if a binding changes, update both this file and
the relevant convention doc.
