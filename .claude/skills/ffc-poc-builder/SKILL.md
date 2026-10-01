---
name: ffc-poc-builder
description: Build sandbox/POC feature modules for the ffc-extension frontend using the SWO design system. Use when the user asks to prototype a dashboard, tab, panel, grid, chart, side-nav shell, or any new feature view driven by mock data. Enforces Storybook-first component sourcing, strongly-typed TS throughout, axios-shaped mocks abstracted behind react-query hooks, and the project's panel/chart/grid conventions.
---

# ffc-extension POC Builder

Goal: ship visually-correct, strongly-typed sandbox views that drop into real backend wiring without a rewrite. Mock data behaves like the API, components never know data is mocked, and the design-system primitives are the ones the real feature will ship with.

Baseline conventions (path aliases, DS subpath imports, TypeScript discipline, Fast Refresh file-split rule, icon/SCSS token hygiene, i18n, verification commands, extraction thresholds) live in **`ffc-frontend-standards`**. This skill only covers POC-specific additions on top.

## Component source priority

1. **Storybook first.** https://storybook.platform.softwareone.com/ — if a widget/recipe matches, use the design-system package it ships from (`@swo/design-system/<subpath>`). Pattern naming in Storybook mirrors the exports (e.g. `widgets-grid--in-memory-example` ↔ `@swo/design-system/grid` `useGridInMemory`).
2. **Partial match → ask.** If the Storybook component covers only part of the behaviour (e.g. `Navigation.SideNav` has the right chrome but can't hold arbitrary children), stop and ask: *"The DS component gives you X but not Y — do you want a custom wrapper, a different DS recipe, or should we open a design-system request?"* Do not invent styles that mimic the DS silently.
3. **External only when nothing fits.** If no DS component covers the need, pick an existing dep (amCharts for charts, react-hook-form for forms) and justify briefly.

## Design-system component gaps (verified)

| Need | Status | What to do |
|---|---|---|
| Multiselect field | ❌ nothing fits. `Select` is single value; `Dropdown` closes on every `onItemSelected`; `SelectableFilter` is modal-heavy and needs an async `apiCall`. | Build from `Popover` + `Checkbox` list (recipe below). |
| Button with `id` / ARIA | ❌ strict `ButtonProps` has no `id` or ARIA passthrough. | For a labelable combobox trigger, use a plain `<button>` with `aria-labelledby` + a visible `<span id>` label. |
| `Icon.name` | ⚠️ strict string-literal union. `arrow_drop_down`, `arrow_down`, etc. don't exist. | Use `expand_more` for dropdowns, `arrow_forward_ios` / `arrow_back_ios` for chevrons, `info`, `filter_alt`. Check `node_modules/@swo/design-system/icon/src/lib/icon-paths/` before guessing. |
| `DonutChart` default size | ⚠️ `height={150}` — tiny in wide panels. | Pass explicit `height={240+}` in large panels. |
| `Navigation.SideNav.groups.items` | ⚠️ strictly link lists; `children` are silently dropped. | Use for navigation only. Form content goes in a sibling panel or a popover triggered from a nav item. |
| `Navigation` default-collapsed | ❌ no prop. | Mount a tiny helper that `requestAnimationFrame`s then `document.querySelector('[data-testid="navigation__collapse-button"]')?.click()`. |
| `Panel` chrome | ⚠️ `Panel` wraps `Card` which already ships padding / radius / background. | Don't restate chrome in `.ffc-panel` or you'll double-pad. |

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

General API-hook conventions live in [`docs/conventions/api-hooks.md`](../../../docs/conventions/api-hooks.md): `useFooApi.tsx` returns raw HTTP callbacks (`{ list, get, save, delete }`), `useFooDetailsApi.ts` wraps `useQuery` with a stable `["<Entity>", "Details", id]` key, consumers import both from the `api/` barrel. **Entity list/detail views in a POC follow those shapes.**

The POC variant below applies to **mock-driven metrics endpoints** — one getter per metric (`getAdoptionMetrics`, …), react-query key `["<Feature>", "<Resource>"]` because metric aggregates aren't entity-centric. The shape is otherwise identical, so the swap to real HTTP is still a one-line change.

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

## POC-specific type notes

Everything in `ffc-frontend-standards` (no `any`, named types in `api/model.ts`, derive via `ComponentProps`/`ReturnType`, barrels re-export runtime + types) applies here. Two POC specifics on top:

- **Chart series + colour arrays are typed** (`XySeriesDef[]`, `number[]`) — amCharts rebuilds its root on identity change, so these must be referentially stable (see "Charts" recipe below).
- **Mock JSON types** go in `api/model.ts` alongside the real response types — the mock *is* the API shape until the real one lands.

## Common recipes

### 12-column panel grid

`.ffc-panel-grid` is a 12-column CSS grid. Panels default to `grid-column: span 6` (half width). Modifiers: `--span-4`, `--span-8`, `--full`. Headline KPI strip sits **outside** the grid as a sibling under `.ffc-tab-stack` (`display:flex; gap:$space-xl`).

```tsx
<div className={"ffc-tab-stack"}>
  <div className={"ffc-kpi-row ffc-kpi-row--four"}>
    {/* headline KPIs */}
  </div>
  <div className={"ffc-panel-grid"}>
    <Panel title={...} className={"ffc-panel--span-4"}>…</Panel>
    <Panel title={...} className={"ffc-panel--span-8"}>…</Panel>
    <Panel title={...} className={"ffc-panel--full"}>…</Panel>
  </div>
</div>
```

### Panel + KPI tiles

```tsx
import { Panel, KpiTile } from "~shared/components/panel";

<Panel title={t("overview:title")}>
  <div className={"ffc-kpi-row"}>  {/* --four / --quad / --column for other layouts */}
    <KpiTile label={t("overview:total")} value={data.total} />
    <KpiTile label={t("overview:active")} value={data.active} trend={"up"} />
  </div>
</Panel>
```

### Linkable KPI tile (navigation affordance)

```tsx
import { PATHS as ORGANIZATION_PATHS } from "~features/organizations/paths";

<KpiTile
  label={t("overview:active")}
  value={data.active}
  trend={"up"}
  linkTo={`${ORGANIZATION_PATHS.root}?status=active`}
/>
```

`linkTo` wraps the Card in a `react-router-dom` `<Link>`, shows an `arrow_forward_ios` chevron on the right, and animates on hover (lift + chevron nudge). The target feature still needs to parse the query param to actually pre-filter its grid — nav + affordance works today.

### Multi-select (compose Popover + Checkbox)

Build this helper once; reuse across filter sidebars. Button-styled trigger with `aria-labelledby`, popover list that stays open across selections.

```tsx
import { useId } from "react";
import { Checkbox } from "@swo/design-system/checkbox";
import { Icon } from "@swo/design-system/icon";
import { Popover } from "@swo/design-system/popover";

type MultiSelectProps<T extends string> = {
  label: string;
  placeholder: string;
  options: { value: T; label: string }[];
  value: T[];
  onChange: (next: T[]) => void;
};

export function MultiSelect<T extends string>({
  label, placeholder, options, value, onChange,
}: MultiSelectProps<T>) {
  const labelId = useId();
  const triggerId = useId();
  const toggle = (v: T) => onChange(value.includes(v) ? value.filter(x => x !== v) : [...value, v]);
  const summary = value.length === 0
    ? placeholder
    : options.filter(o => value.includes(o.value)).map(o => o.label).join(", ");

  return (
    <div className={"ffc-multiselect"}>
      <span id={labelId} className={"ffc-multiselect__label"}>{label}</span>
      <Popover trigger={"click"} keepOpenOnOutsideClick={false}>
        <Popover.Target>
          <button
            type={"button"}
            id={triggerId}
            className={"ffc-multiselect__trigger"}
            aria-labelledby={`${labelId} ${triggerId}`}
            aria-haspopup={"listbox"}
          >
            <span className={"ffc-multiselect__summary"}>{summary}</span>
            <Icon name={"expand_more"} size={16} />
          </button>
        </Popover.Target>
        <Popover.Content>
          <div className={"ffc-multiselect__list"} role={"listbox"} aria-multiselectable>
            {options.map(o => (
              <Checkbox
                key={o.value}
                label={o.label}
                isChecked={value.includes(o.value)}
                onChange={() => toggle(o.value)}
              />
            ))}
          </div>
        </Popover.Content>
      </Popover>
    </div>
  );
}
```

Why not `Dropdown`: it fires `isOpenChange(false)` on every `onItemSelected`, closing the list after each tick — poor multi-select UX.

### Charts — module-scope series for referential stability

```tsx
// Module scope: amCharts rebuilds the root on series/colors identity change.
const SERIES: XySeriesDef[] = [
  { field: "spend", name: "Spend", color: CHART_COLORS.blue, kind: "line" },
];
```

Shared primitives: `XyChart` (line/area/column, `stacked`, `horizontal`), `DonutChart`, `ChartLegend`. Palette: `CHART_COLORS` + `PROVIDER_COLORS` from `~shared/components/charts`. Pass explicit `height` to `DonutChart` in wide panels (default 150 looks tiny).

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

**`GridFilterFieldType` values** (grep `@swo/design-system/grid/src/lib/model.d.ts`): `'text' | 'number' | 'date' | 'datetime' | 'boolean' | 'list'`. `list` requires `options: {value, label}[]` — the stored row value is compared as a **string**, so don't use `list` for numeric columns (e.g. a maturity-level 0-4) unless you're willing to store the value as a string too; use `number` instead.

Date columns: store ISO in the mock, format in the cell with `useFormatDate` from `~shared/hooks/useFormatDate`. Chips (`@swo/design-system/chip`) with `color="success"|"warning"|"gray"|"primary"` for status/threshold indicators — default `type` is filled; use `type="outline"` only when the storybook default doesn't fit.

### Modals + wizards

Follow [`docs/conventions/modals.md`](../../../docs/conventions/modals.md). Simple create-entity form → `Create<Entity>Modal.tsx` wrapping `<Modal>` + `useModalToggle` + `use<Entity>FormController` (shared mutation + close plumbing). Multi-step flow → a `<flow>-wizard/` folder with a single component rendering `@swo/design-system/wizard` inside `@swo/design-system/modal`'s `<Modal>`; owns its own `react-hook-form` + mutation across steps, no form controller.

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

Collapsed-by-default: no prop. Mount a tiny helper that `requestAnimationFrame`s then clicks `[data-testid="navigation__collapse-button"]`.

### Collapse / expand animation + chevron rotation

For a header that reveals a form body, prefer `max-height` over the grid-rows trick — it reliably clips intrinsic-sized content:

```scss
.panel__body {
  max-height: 0;
  overflow: hidden;
  visibility: hidden;
  transition:
    max-height 0.25s ease,
    visibility 0s linear 0.25s;

  &--open {
    max-height: 640px;
    overflow: visible;    // let popovers escape once settled
    visibility: visible;
    transition:
      max-height 0.25s ease,
      visibility 0s linear 0s;
  }
}
```

Rotate a single chevron with `transform: rotate(90deg)` instead of swapping to a second icon — one asset, smoother:

```scss
.panel__chevron {
  transition: transform 0.2s ease;
  &--open { transform: rotate(90deg); }
}
```

### Styles

- Shared feature-grid primitives live in `src/shared/styles/_components.scss` under the `.ffc-*` namespace.
- Use existing classes before adding: `.ffc-tab-stack`, `.ffc-panel-grid`, `.ffc-panel`, `.ffc-panel--full`, `.ffc-panel--span-4`, `.ffc-panel--span-8`, `.ffc-kpi-row`, `.ffc-kpi-row--four`, `.ffc-kpi-row--quad`, `.ffc-kpi-row--column`, `.ffc-chart-split`, `.ffc-chart-split--triple`, `.ffc-legend`, `.ffc-filter-bar`, `.ffc-multiselect`.
- Add modifiers (`&--variant`) rather than one-off component CSS.

## Scaling the POC (iteration 2+)

The first draft of a POC follows the "feature folder layout" above. These patterns kick in once the feature has multiple tabs, repeated panels, or starts to need interactive filtering. Apply them *when* the duplication appears — not pre-emptively.

### Collapse repeated react-query hooks into a factory

If three or more resources have the same hook body (same `useQuery` plumbing, only key + fetcher differ), collapse them:

```ts
type DashboardApi = ReturnType<typeof useDashboardApi>;
type Fetcher<T> = (filters: DashboardFilters) => Promise<AxiosResponse<T>>;

function createMetricsQuery<T>(key: string, select: (api: DashboardApi) => Fetcher<T>) {
  return function useMetricsQuery() {
    const { filters } = useDashboardFilters();
    const fetcher = select(useDashboardApi());
    return useQuery({
      queryKey: ["Dashboard", key, filters] as const,
      queryFn: async () => (await fetcher(filters)).data,
    });
  };
}

export const useAdoptionMetricsApi = createMetricsQuery("AdoptionMetrics", (api) => api.getAdoptionMetrics);
export const useConsumptionMetricsApi = createMetricsQuery("ConsumptionMetrics", (api) => api.getConsumptionMetrics);
```

Named exports stay the same so consumers don't change. Adding a new metric = one line.

### Centralised chart config + height scale

When two or more tabs each declare module-scope `*_SERIES`, `*_COLORS`, pull them into a `chartConfig.ts` sibling to the feature config:

```ts
// features/<feature>/chartConfig.ts
export const CHART_HEIGHT = { xs: 190, sm: 200, md: 220, lg: 260 } as const;

export const PROVIDER_TREND_SERIES: XySeriesDef[] = [ /* ... */ ];
export const STATUS_DONUT_COLORS = [CHART_COLORS.green, CHART_COLORS.orange, CHART_COLORS.gray];
```

Pick the `CHART_HEIGHT` scale to match the pixel values already in use so the refactor is visually non-breaking. One file to change for a palette or sizing update.

### `<MetricPanel>` composition

When the Panel > optional KPI row > optional chart-split (trend + aside donut) pattern repeats 3+ times, extract:

```tsx
type MetricPanelProps = {
  title: string;
  className?: string;
  description?: string;
  kpis?: KpiTileProps[];       // config array — renders ffc-kpi-row internally
  trend?: ReactNode;           // left side of chart-split
  aside?: ReactNode;           // right side (usually a DonutChart)
  asideLabel?: string;         // optional heading above aside
  children?: ReactNode;        // escape hatch for unusual layouts
};
```

If `trend` or `aside` is provided, the component wraps them in `.ffc-chart-split` + `.ffc-chart-split__aside` internally. For truly bespoke layouts (e.g. inverted split with donut on the left), use `children` — don't bend the component with an orientation prop for a single case.

### Wired filter sidebar (draft/apply)

Local filter state only looks interactive. To make Apply real:

1. **Context** owns the applied filters (`filters`, `setFilters`).
2. **Sidebar** keeps a `draft` state initialised from context; Apply commits `draft → setFilters`.
3. **Query hooks** read `useFooFilters()`, include filters in the `queryKey`, and pass them into the getter. React-query refetches automatically.
4. **Mock getter** accepts `(filters)` for signature uniformity. Apply **one visible transform** (e.g. filter one grid by status) to prove the plumbing — don't try to filter every chart. Extend as stakeholder demos require it.
5. **Collapsed summary** shows the **applied** counts, not the draft, so the header matches what's actually visible in charts.

### Real-API swap seam comment

Put a header comment at the top of `useFeatureApi.ts` documenting the one-line swap:

```ts
// Real-API swap seam. `mockResponse(json)` returns the same `AxiosResponse<T>` shape as
// `http<T>({ method: "GET", url })` from `@mpt-extension/sdk` (see useEntitlementsApi.tsx),
// so each getter body is a one-line swap:
//   mockResponse(adoptionMetrics as AdoptionMetrics)
//     → http<AdoptionMetrics>({ method: "GET", url: `/ops/v1/dashboard/adoption?${qs(filters)}` })
// The getter signatures stay stable, so metricsQueries.ts and the tabs don't change.
```

Points the next person at the live reference instead of making them guess.

### Domain enums live in `api/model.ts`, not in React files

Const tuples + derived unions for domain values (`ORGANISATION_STATUSES`, `CLOUD_PROVIDERS`, `BILLING_STATUSES`) belong in `api/model.ts`. React files (context, sidebar) import them. Rationale: model has no React deps, so the dependency arrow points one way (React → model). Avoids the awkward "why is my status enum in a context file" question six weeks later.

### When NOT to abstract (seen tried, dropped)

- **`ListResponse<T>` promotion** — only promote when *this feature* uses paginated lists. A shared one already exists at `~shared/utils/mapAxiosResponseDataList.tsx` (`items?: T[]`). `features/organizations/api/*` has local duplicates with an incompatible shape (`data?: T[]`). Reconciling them touches live production code and is a separate feature-level cleanup — don't fold it into a POC refactor.
- **Narrowing `DistributionSlice.category`** — if the mock values are display strings (`"Azure"`, `"Active"`, `"Level 0"`) rather than identifiers, union-narrowing buys nothing: chart legends consume them as plain text, no logic keys off them.

## New POC checklist

1. **Component sourcing** — scan Storybook for each UI element; ask on partial match before inventing.
2. **Types first** — add `type`s / enums to `api/model.ts` before the hook or JSON.
3. **Mock JSON** — exact shape of the type, realistic values, ISO dates for sortable fields.
4. **API hooks** — low-level getter in `useFeatureApi`, react-query wrapper per resource, index barrel export.
5. **Tab/component** — consume the hook, `if (!data) return null`, module-scope any amCharts config.
6. **i18n** — all strings via `useFixedT`, keys alphabetised.
7. **Styles** — reuse `.ffc-*` classes; add modifiers in `_components.scss` instead of local overrides.
8. **Verify** — `cd frontend && npm run typecheck` **and** `npm run build` (SCSS errors only show at build); run `npx prettier --write` on touched files.

## Iteration rhythm for POC work

POC sessions are visual-iteration heavy. The user rolls back layout decisions ~1 in 3 times. To keep churn low:

- **Propose + ask on design-trade-off decisions.** Panel order, column spans, chart heights, chip variants, filter placement, hover styles — present one option with a one-line rationale and wait, don't commit silently.
- **Keep each change tightly scoped.** One concern per iteration (grid ratios, OR KPI typography, OR hover effect) — mixing them makes rollback expensive.
- **Trust the roll-back.** If asked to revert, do it cleanly (not partially) and remove orphaned i18n keys / SCSS blocks / imports in the same step.

## POC anti-patterns

(General ones — root DS imports, Fast-Refresh split, guessing icon/SCSS names, premature extraction — live in `ffc-frontend-standards`.)

- Importing JSON directly in a tab/component — breaks the swap-to-real-API story.
- Inline response shapes in a tab/component — belongs in `api/model.ts`.
- Rebuilding chart series arrays inside the component body — triggers amCharts root rebuild on every render; keep them at module scope.
- Custom chrome that mimics DS primitives — if it looks like a `Navigation.CollapseButton` it must be one, otherwise ask.
- Using `Dropdown` for multi-value — closes on each selection; use the `Popover` + `Checkbox` multi-select recipe instead.
- `grid-template-rows: 0fr → 1fr` for height animation — intrinsic-sized form controls leak out of the clipped row in some browsers; use `max-height` + `overflow:hidden` + `visibility` instead.
- Re-adding an import to a file whose target was previously deleted — check with the Grep tool before trusting a paste.
