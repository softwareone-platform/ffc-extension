---
name: ffc-poc-builder
description: Build sandbox/POC feature modules for the ffc-extension frontend using the SWO design system. Use when the user asks to prototype a dashboard, tab, panel, grid, chart, side-nav shell, or any new feature view driven by mock data. Enforces Storybook-first component sourcing, strongly-typed TS throughout, axios-shaped mocks abstracted behind react-query hooks, and the project's panel/chart/grid conventions.
---

# ffc-extension POC Builder

Goal: ship visually-correct, strongly-typed sandbox views that drop into real backend wiring without a rewrite. Mock data behaves like the API, components never know data is mocked, and the design-system primitives are the ones the real feature will ship with.

## Component source priority

1. **Storybook first.** https://storybook.platform.softwareone.com/ — if a widget/recipe matches, use the design-system package it ships from (`@swo/design-system/<subpath>`). Pattern naming in Storybook mirrors the exports (e.g. `widgets-grid--in-memory-example` ↔ `@swo/design-system/grid` `useGridInMemory`).
2. **Partial match → ask.** If the Storybook component covers only part of the behaviour (e.g. `Navigation.SideNav` has the right chrome but can't hold arbitrary children), stop and ask: *"The DS component gives you X but not Y — do you want a custom wrapper, a different DS recipe, or should we open a design-system request?"* Do not invent styles that mimic the DS silently.
3. **External only when nothing fits.** If no DS component covers the need, pick an existing dep (amCharts for charts, react-hook-form for forms) and justify briefly.

Known gaps worth remembering: `Navigation.SideNav.groups.items` are strictly link lists (no form content); `Navigation` has no `defaultCollapsed` prop (toggle via the auto-rendered `[data-testid="navigation__collapse-button"]` after `requestAnimationFrame`).

## Feature folder layout

```
features/<feature>/
├── <Feature>.tsx            # route shell (Navigation + Outlet)
├── paths.ts                 # SEGMENTS + absolute PATHS consts
├── tabs/                    # one component per sub-route view
├── components/              # feature-local components (sidebars, cells, dialogs)
├── api/
│   ├── model.ts             # all response types / enums / row types
│   ├── use<Feature>Api.ts   # low-level axios-shaped mocks
│   ├── use<Resource>Api.ts  # react-query hook per resource
│   └── index.ts             # barrel: `export * from "./model"` + hooks
└── mock/<resource>.json     # one fixture per endpoint, shape = the API type
```

**Rules**
- Tabs/components import the react-query hook; they never see mock JSON.
- `use<Feature>Api` is the single swap point for real HTTP — one file to change later.
- JSON file names mirror the hook name (`consumption.json` ↔ `useConsumptionMetricsApi`).

## Data layer recipe

**Mock JSON — must mirror the real API shape.** Dates ISO (`YYYY-MM-DD`) for sortable fields, display formatting happens in the cell. Numeric metrics stay numeric; preformatted strings only when the API itself returns strings.

**Low-level API hook** (`api/useDashboardApi.ts` pattern):

```ts
import { useCallback, useMemo } from "react";
import { AxiosResponse } from "axios";
import { mockResponse } from "~shared/utils/mockResponse";
import adoptionMetrics from "../mock/adoption.json";
import { AdoptionMetrics } from "./model";

export function useDashboardApi() {
  const getAdoptionMetrics = useCallback(
    (): Promise<AxiosResponse<AdoptionMetrics>> => mockResponse(adoptionMetrics as AdoptionMetrics),
    [],
  );
  return useMemo(() => ({ getAdoptionMetrics }), [getAdoptionMetrics]);
}
```

`mockResponse(data, 250)` from `~shared/utils/mockResponse` returns an axios-shaped promise with a 250 ms delay so components exercise loading states.

**Per-resource react-query hook** — thin, cache key under feature namespace:

```ts
export function useAdoptionMetricsApi() {
  const { getAdoptionMetrics } = useDashboardApi();
  return useQuery({
    queryKey: ["Dashboard", "AdoptionMetrics"] as const,
    queryFn: async () => (await getAdoptionMetrics()).data,
  });
}
```

**Component consumption** — stay out of data-source knowledge:

```ts
const { data } = useAdoptionMetricsApi();
if (!data) return null;
```

## TypeScript discipline (strongly typed everywhere)

- **Every API response is a named `type`** in `api/model.ts`. Avoid inline shapes.
- **Enums or string-literal unions** for finite categorical values (`status: "trial" | "paid"`), never `string`.
- **No `any`** — use `unknown` and narrow, or a precise type.
- **Chart series arrays and colour arrays are typed** (`XySeriesDef[]`, `number[]`).
- **Row types are shared** between the API model, the grid, and any cell renderer.
- **Props on helper components** always declared, even for one-prop wrappers.
- **Barrels re-export both runtime + types** (`export type { Foo }`, `export { useFoo }`).

Example row + typed enum:

```ts
export type OrgWithoutDatasourceRow = {
  id: string;
  organizationName: string;
  creationDate: string;       // ISO
  status: OrgSubscriptionStatus;
  daysSinceCreation: number;
};
export type OrgSubscriptionStatus = "trial" | "paid";
```

## Design-system import discipline

- **Always subpath**: `@swo/design-system/button`, `@swo/design-system/grid`, `@swo/design-system/chip`, `@swo/design-system/navigation`, etc. Never root `@swo/design-system`.
- **Why**: subpath imports cost 100s of KB each; root import pulls everything (see `project-frontend-bundle-facts` memory).
- **Design tokens**: `@swo/design-tokens` — only in SCSS. In amCharts configs use raw hex via `CHART_COLORS` because tokens are CSS vars that haven't resolved yet.

## Common recipes

### Panel + KPI tiles

```tsx
import { Panel, KpiTile } from "~shared/components/panel";

<Panel title={t("overview:title")}>
  <div className={"ffc-kpi-row"}>  {/* or ffc-kpi-row--quad for 4 KPIs */}
    <KpiTile label={t("overview:total")} value={data.total} />
    <KpiTile label={t("overview:active")} value={data.active} trend={"up"} />
  </div>
</Panel>
```

### Charts — module-scope series for referential stability

```tsx
// Module scope: amCharts rebuilds the root on series/colors identity change.
const SERIES: XySeriesDef[] = [
  { field: "spend", name: "Spend", color: CHART_COLORS.blue, kind: "line" },
];
```

Shared primitives: `XyChart` (line/area/column, `stacked`, `horizontal`), `DonutChart`, `ChartLegend`. Palette: `CHART_COLORS` + `PROVIDER_COLORS` from `~shared/components/charts`.

### Grid (in-memory) with initial sort

```tsx
const INITIAL_SORT: GridFieldSortOperation[] = [{ field: "creationDate", direction: "desc" }];

const columns = useMemo((): GridColumnDefinition<Row>[] => [ /* ... */ ], [deps]);
const fields = useMemo((): GridFieldDefinition[] => [
  { name: "creationDate", title: t("creationDate"), type: "date" },
  { name: "daysSinceCreation", title: t("daysSinceCreation"), type: "number" },
  { name: "status", title: t("status"), type: "text" },
], [t]);

const gridProps = useGridInMemory<Row>(rows, {
  id: "grid__<feature>-<entity>",   // stable id, feature__entity casing
  columns,
  fields,                           // required for sort/filter comparisons
  sort: INITIAL_SORT,
});
return <Grid<Row> {...gridProps} />;
```

Date columns: store ISO in the mock, format in the cell with `useFormatDate` from `~shared/hooks/useFormatDate`. Chips (`@swo/design-system/chip`) with `color="success"|"warning"|"gray"|"primary"` for status/threshold indicators.

### Navigation shell

```tsx
<Navigation>
  <Navigation.SideNav level={1} groups={sideNavGroups} />
  <Navigation.Content>
    <Navigation.TopBar items={topBarItems} />
    <Outlet />
  </Navigation.Content>
</Navigation>
```

Collapsed-by-default: there is no prop. Mount a tiny helper that `requestAnimationFrame`s then `document.querySelector('[data-testid="navigation__collapse-button"]')?.click()`.

### i18n

- Namespace: `"<feature>": { ... }` in `src/i18n/en.json`.
- Access: `const t = useFixedT("<feature>:<section>")` then `t("key")` — one hook per section used, not one for the whole feature.
- Keys sorted alphabetically within each object (the `translations:sort` script enforces this).

### Styles

- Shared feature-grid primitives live in `src/shared/styles/_components.scss` under the `.ffc-*` namespace.
- Use existing classes before adding: `.ffc-panel-grid`, `.ffc-panel`, `.ffc-panel--full`, `.ffc-kpi-row`, `.ffc-kpi-row--quad`, `.ffc-chart-split`, `.ffc-chart-split--triple`, `.ffc-legend`, `.ffc-filter-sidebar`.
- Add modifiers (`&--variant`) rather than one-off component CSS.

## New POC checklist

1. **Component sourcing** — scan Storybook for each UI element; ask on partial match before inventing.
2. **Types first** — add `type`s / enums to `api/model.ts` before the hook or JSON.
3. **Mock JSON** — exact shape of the type, realistic values, ISO dates for sortable fields.
4. **API hooks** — low-level getter in `useFeatureApi`, react-query wrapper per resource, index barrel export.
5. **Tab/component** — consume the hook, `if (!data) return null`, module-scope any amCharts config.
6. **i18n** — all strings via `useFixedT`, keys alphabetised.
7. **Styles** — reuse `.ffc-*` classes; add modifiers in `_components.scss` instead of local overrides.
8. **Verify** — `cd frontend && npm run typecheck` must pass; run `npx prettier --write` on touched files.

## Anti-patterns

- Importing JSON directly in a tab/component — breaks the swap-to-real-API story.
- Hardcoded strings in JSX — breaks i18n.
- Inline `type: "number"` fields in react-query payloads — belongs in `model.ts`.
- Rebuilding chart series arrays inside the component body — triggers amCharts root rebuild on every render.
- Root `@swo/design-system` imports — bundle size regression.
- Custom chrome that mimics DS primitives — if it looks like a Navigation.CollapseButton it must be one, otherwise ask.
