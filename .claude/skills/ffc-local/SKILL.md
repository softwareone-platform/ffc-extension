---
name: ffc-local
description: Project-specific bindings for ffc-extension (the local MPT project). Resolves concrete values the mpt-* skills reference abstractly — alias names, CSS prefix, shared wrapper paths, shared hook names, test-utils inventory, entity list, i18n namespaces, SCSS class list, project scripts. Use whenever any frontend task touches ffc-extension — in combination with mpt-frontend-standards, mpt-design-system, mpt-poc-builder, or mpt-module-testing. In another MPT project this file is replaced by that project's own `*-local` skill with its own bindings.
---

# ffc-extension project bindings

The `mpt-*` skills are written to be portable across MPT frontend projects.
When they reference "the project's shared panel wrapper" or "the project's
test-utils factories", resolve those names using the table below.

In another MPT project this file is replaced by `vikings-local` /
`<project>-local` / … with that project's own bindings.

## TS path aliases

Configured in `frontend/tsconfig.json` + `frontend/jest.config.js`. Always
import by alias — never climb `../../../`.

| Alias           | Points at                       | Use for                                                                    |
| --------------- | ------------------------------- | -------------------------------------------------------------------------- |
| `~shared/*`     | `frontend/src/shared/*`         | Hooks, utils, UI primitives, styles, mock helpers reused across features   |
| `~features/*`   | `frontend/src/features/*`       | Cross-feature references (e.g. `~features/organizations/paths`)            |
| `~api/*`        | `frontend/src/api/*`            | Generated / shared API types (`ffc-api-model`)                             |
| `~test-utils/*` | `frontend/src/test-utils/*`     | Render wrappers, factories, shared jest mocks — spec files only            |

## CSS prefix

Shared presentation classes use the `.ffc-*` namespace. Defined in
[`frontend/src/shared/styles/_components.scss`](../../../frontend/src/shared/styles/_components.scss).

Known classes:

- **Tab + panel layout:** `.ffc-tab-stack`, `.ffc-panel-grid`, `.ffc-panel`,
  `.ffc-panel--full`, `.ffc-panel--span-4`, `.ffc-panel--span-8`
- **KPI rows:** `.ffc-kpi-row`, `.ffc-kpi-row--four`, `.ffc-kpi-row--quad`,
  `.ffc-kpi-row--column`
- **Chart composition:** `.ffc-chart-split`, `.ffc-chart-split--triple`, `.ffc-legend`
- **Filter affordances:** `.ffc-filter-bar`, `.ffc-multiselect`

## Shared wrappers (`~shared/components/*`)

| Area                | Import from                             | Public exports                                                                |
| ------------------- | --------------------------------------- | ----------------------------------------------------------------------------- |
| Panel + KpiTile     | `~shared/components/panel`              | `Panel`, `KpiTile`, `KpiTileProps`                                             |
| Charts              | `~shared/components/charts`             | `XyChart`, `DonutChart`, `ChartLegend`, `CHART_COLORS`, `PROVIDER_COLORS`, `XySeriesDef` |
| Modal               | `~shared/components/modal/Modal`        | `Modal`; cancel action from `~shared/components/modal/ModalCancelButton`      |

## Shared hooks (`~shared/hooks/*`)

| Hook                           | Purpose                                                             |
| ------------------------------ | ------------------------------------------------------------------- |
| `useFixedT(prefix)`            | i18n wrapper around `useTranslation` with a fixed key prefix        |
| `useFormatDate()`              | Locale-aware date formatter for grid cells                           |
| `useModalToggle({ onSuccess })` | In-app modal open/close state with a success callback               |

## Shared utils (`~shared/utils/*`)

| Util                                  | Purpose                                                              |
| ------------------------------------- | -------------------------------------------------------------------- |
| `mockResponse(data, delayMs?)`        | Axios-shaped mock response — the swap seam for real `http<T>()`      |
| `mapAxiosResponseDataList` (`ListResponse<T>`) | Shared list-response envelope type (`items?: T[]`)          |

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

- `organizations/` — organization CRUD + details (users, data sources, events)
- `entitlements/` — entitlement list, details, create wizard
- `dashboard/` — sandbox POC dashboard (mock-driven)

Entity grid route helpers:

- `renderWithEntitlementRoute(ui, { id, routePath })`
- `renderWithOrganizationRoute(ui, { id, routePath })`

Entity factories (typed `Partial<T>` builders):

- `makeOrganization`, `makeEntitlement`, `makeEmployee`, `makeDatasource`, `makeAccount`

## i18n

- **Hook:** `useFixedT(prefix)` from `~shared/hooks/useFixedT`
- **Resource file:** `frontend/src/i18n/en.json`
- **Top-level namespaces:** `organization`, `entitlement`, `shared`, `dashboard`
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
