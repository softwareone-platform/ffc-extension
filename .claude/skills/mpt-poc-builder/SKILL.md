---
name: mpt-poc-builder
description: Build sandbox / POC feature modules for an MPT frontend project using the SWO design system. Use when the user asks to prototype a dashboard, tab, panel, grid, chart, side-nav shell, or any new feature view driven by mock data. Enforces Storybook-first component sourcing, strongly-typed TS throughout, axios-shaped mocks abstracted behind react-query hooks, and the project's panel / chart / grid conventions.
---

# MPT POC Builder

Goal: ship visually-correct, strongly-typed sandbox views that drop into real backend wiring without a rewrite. Mock data behaves like the API, components never know data is mocked, and the design-system primitives are the ones the real feature will ship with.

Baseline conventions (path aliases, TypeScript discipline, Fast Refresh file-split, verification commands, extraction thresholds) live in **`mpt-frontend-standards`**. Design-system component usage (Panel + KpiTile, Grid, Modal, Charts, Multi-select, Chip, DatePicker, Navigation) lives in **`mpt-design-system`** + [`docs/conventions/design-system-components.md`](../../../docs/conventions/design-system-components.md). DS meta rules (subpath imports, verified gaps, icons, SCSS tokens, shared layout classes, chart palettes) live in [`docs/conventions/design-system.md`](../../../docs/conventions/design-system.md). Concrete project bindings (alias names, CSS prefix, wrapper paths, entity list) live in the active project's project bindings skill — in ffc-extension that's [`ffc-extension`](../ffc-extension/SKILL.md). This skill only covers POC-specific additions on top of all that.

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

**Low-level API hook** (`api/useFooApi.ts` pattern). The POC needs a tiny `mockResponse` helper that wraps the JSON fixture in an `AxiosResponse` shape — the project does not ship one, so add it under the POC feature folder (or in `~shared/utils/` if you expect other features to need it):

```ts
// features/<feature>/api/mockResponse.ts  (or ~shared/utils if promoted)
import { AxiosResponse } from "axios";

export function mockResponse<T>(data: T, delayMs = 250): Promise<AxiosResponse<T>> {
  return new Promise((resolve) =>
    setTimeout(() => resolve({ data } as AxiosResponse<T>), delayMs),
  );
}
```

Then the feature API hook uses it:

```ts
import { useCallback, useMemo } from "react";
import { AxiosResponse } from "axios";

import adoptionMetrics from "../mock/adoption.json";
import { mockResponse } from "./mockResponse";
import { AdoptionMetrics } from "./model";

export function useDashboardApi() {
  const getAdoptionMetrics = useCallback(
    (): Promise<AxiosResponse<AdoptionMetrics>> => mockResponse(adoptionMetrics as AdoptionMetrics),
    [],
  );
  return useMemo(() => ({ getAdoptionMetrics }), [getAdoptionMetrics]);
}
```

The 250 ms delay lets react-query components exercise their loading states. The whole helper is throwaway — once the real HTTP endpoint lands, swap `mockResponse(...)` for `http<T>({ method: "GET", url })` and delete the helper.

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

Everything in `mpt-frontend-standards` (no `any`, named types in `api/model.ts`, derive via `ComponentProps`/`ReturnType`, barrels re-export runtime + types) applies here. Two POC specifics on top:

- **Chart series + colour arrays are typed** (use the project's chart series type if one exists, otherwise a local `type Series = { field: string; name: string; color: string; kind: "line" | "area" | "column" }[]`) — amCharts rebuilds its root on identity change, so these must be referentially stable (see the shared Charts section in [`docs/conventions/design-system-components.md`](../../../docs/conventions/design-system-components.md)).
- **Mock JSON types** go in `api/model.ts` alongside the real response types — the mock *is* the API shape until the real one lands.

## Common recipes

### 12-column panel grid

The project's shared `panel-grid` class is a 12-column CSS grid. Panels default to `grid-column: span 6` (half width). Modifiers: `--span-4`, `--span-8`, `--full`. Headline KPI strip sits **outside** the grid as a sibling under the project's `tab-stack` class (`display:flex; gap:$space-xl`). Concrete class names (ffc-extension uses `.ffc-tab-stack`, `.ffc-panel-grid`, `.ffc-panel`, `.ffc-panel--span-N`, `.ffc-panel--full`) are in [`ffc-extension`](../ffc-extension/SKILL.md). In the snippet below, `${PFX}` stands for the project's shared class prefix (resolve via your project bindings skill).

```tsx
<div className={`${PFX}-tab-stack`}>
  <div className={`${PFX}-kpi-row ${PFX}-kpi-row--four`}>
    {/* headline KPIs */}
  </div>
  <div className={`${PFX}-panel-grid`}>
    <Panel title={...} className={`${PFX}-panel--span-4`}>…</Panel>
    <Panel title={...} className={`${PFX}-panel--span-8`}>…</Panel>
    <Panel title={...} className={`${PFX}-panel--full`}>…</Panel>
  </div>
</div>
```

### DS component recipes (Panel+KpiTile, Grid, Modal, Charts, Multi-select, Navigation)

Moved to [`docs/conventions/design-system-components.md`](../../../docs/conventions/design-system-components.md) + the **`mpt-design-system`** skill. Both apply to POC and production. The POC-specific additions below (12-column grid, scaling patterns, iteration rhythm) build on top.

### Chart hover tooltips (amCharts XyChart)

Stakeholders will ask "what's the value here?" on every demo. Attach tooltips on the series template, add bullets on line/area series so the hover target isn't a 2px stroke, and add a shared crosshair so the tooltip appears even when the cursor isn't dead-centre on a bar/bullet:

```ts
const tooltipText = horizontal ? "[bold]{name}[/]\n{valueX}" : "[bold]{name}[/]\n{valueY}";

// Column series — tooltip on the column template itself
columnSeries.columns.template.setAll({
  tooltipText,
  /* …fillOpacity, width, strokeOpacity… */
});

// Line / area series — bullets double as hover targets
lineSeries.bullets.push(() =>
  am5.Bullet.new(root, {
    sprite: am5.Circle.new(root, {
      radius: 4,
      fill: am5.color(def.color),
      stroke: am5.color(0xffffff),
      strokeWidth: 2,
      tooltipText,
    }),
  }),
);

// Shared series tooltip (background + text styling)
function attachTooltip(entry: am5xy.XYSeries) {
  entry.set("tooltip", am5.Tooltip.new(root, {
    labelText: tooltipText,
    autoTextColor: false,
    getFillFromSprite: false,
    pointerOrientation: "horizontal",
  }));
  const tooltip = entry.get("tooltip");
  tooltip?.get("background")?.setAll({ fill: am5.color(0xffffff), fillOpacity: 0.95, stroke: am5.color(0xe0e5e8) });
  tooltip?.label.setAll({ fill: am5.color(0x25282d), fontSize: 12 });
}

// Chart-level crosshair cursor so hovering a column anywhere in its category still fires the tooltip
chart.set("cursor", am5xy.XYCursor.new(root, { behavior: "none", xAxis, yAxis }));
```

Keep `tooltipText` and `attachTooltip` module-scoped in `XyChart.tsx` so they're applied once per series created in the structural effect — not inside the data-update effect, which would re-attach on every refetch.

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

Shared presentation class inventory + add-modifier rule live in [`docs/conventions/design-system.md`](../../../docs/conventions/design-system.md). The concrete class prefix (e.g. `.ffc-*`) and full class list are in the project's project bindings skill.

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

export const PROVIDER_TREND_SERIES = [ /* ... */ ] as const;
export const STATUS_DONUT_COLORS = ["#1aa363", "#f26b1f", "#8a8a8a"] as const;
```

Pick the `CHART_HEIGHT` scale to match the pixel values already in use so the refactor is visually non-breaking. One file to change for a palette or sizing update.

### `<MetricPanel>` composition

When the Panel > optional KPI row > optional chart-split (trend + aside donut) pattern repeats 3+ times, extract:

```tsx
type MetricPanelProps = {
  title: string;
  className?: string;
  description?: string;
  kpis?: KpiTileProps[];       // config array — renders the project's shared kpi-row class internally
  trend?: ReactNode;           // left side of chart-split
  aside?: ReactNode;           // right side (usually a DonutChart)
  asideLabel?: string;         // optional heading above aside
  children?: ReactNode;        // escape hatch for unusual layouts
};
```

If `trend` or `aside` is provided, the component wraps them in the project's `chart-split` + `chart-split__aside` classes internally. For truly bespoke layouts (e.g. inverted split with donut on the left), use `children` — don't bend the component with an orientation prop for a single case.

### Wired filter sidebar (mixed live-apply + draft/apply)

Local filter state only looks interactive. To make it real, use a **mixed** apply model — not a sticky "Apply" button for everything:

1. **Context** owns the applied filters (`filters`, `setFilters`).
2. **Simple inputs (multi-selects, single toggles) → live-apply.** Write straight to context on `onChange`. A sticky Apply button for routine picks is friction.
3. **Compound inputs (date range) → draft + Apply inside the input's own popover.** A range is only valid once both ends are set; keep an internal draft so a half-finished pick doesn't commit a broken filter. Preset shortcuts (This month / Last month / etc.) → one-click apply + close popover; no draft for those, they're explicit intents.
4. **Query hooks** read `useFooFilters()`, include filters in the `queryKey`, and pass them into the getter. React-query refetches automatically.
5. **`placeholderData: keepPreviousData` is mandatory.** Without it, every filter change makes the `if (!data) return null` guard unmount the whole panel grid, amCharts restarts its load animation, and the dashboard appears to full-reload. With it, previous data stays rendered during refetch so changes feel like a refresh, not a reload.
6. **Loading overlay** — compose from `useIsFetching({ queryKey: ["<Feature>"] })` + an absolutely-positioned div over the content, with the DS `LoadingSpinner` centred. Overlay + `keepPreviousData` together give the "refreshing on top of last data" affordance the DS doesn't ship.
7. **Mock getter** accepts `(filters)` for signature uniformity. For "one visible transform to prove the plumbing", see the next section (**Mock-side reactivity patterns**) — a scalar + per-dimension filter pass is often less work than it looks.

### Mock-side reactivity patterns

"Apply one visible transform" undersells how much a POC needs — stakeholders tend to pick filters at random to kick the tyres, and if any card doesn't react they report it as broken. A **three-layer** pipeline covers almost every demo cleanly:

**1. Scalar `computeScale(filters)` for KPIs + non-distribution charts.**

Multiply each dimension's selected shares to a single factor, then walk the whole payload and scale every numeric field with a `transformMetrics(data, scale, months)` helper:

```ts
function computeScale(filters: DashboardFilters): number {
  const statusScale = filters.statuses.length === 0 || filters.statuses.length === ALL_STATUSES.length
    ? 1
    : filters.statuses.reduce((sum, s) => sum + STATUS_SHARE[s], 0);
  const providerScale = /* …same shape… */;
  const dateScale = rangeMonths(filters) / BASELINE_MONTHS; // longer range → higher totals
  return statusScale * providerScale * dateScale;
}

// Deep-walk the mock, scale numeric fields, leave labels/percentages/dates alone.
function transformMetrics<T>(value: T, scale: number, months: number): T {
  if (typeof value === "number") return Math.round(value * scale) as T;
  if (typeof value === "string") {
    // "$1,250" → "$5,000", "412" → "1,648", "98%"/"−1.2%" → left alone (ratios, not totals).
    …
  }
  if (Array.isArray(value)) return maybeTailMonthlySeries(value, months, scale);
  if (value && typeof value === "object") return mapObject(value, scale, months);
  return value;
}
```

**2. Monthly windowing** — tail monthly chart arrays (`{ month | period | bucket, …fields }` rows) to the actual range length, capped at the mock's series length. Without this, the x-axis is static even when values move, and users think "nothing changed" even though the headline KPIs did.

```ts
const sliced = isMonthlySeries ? mapped.slice(-months) : mapped;
```

**3. Per-dimension `filterXView(data, filters)` passes — mandatory for distribution donuts.** Uniform scaling preserves ratios, so the pie slices look identical when every slice shrinks by the same factor. Users read this as "the donut's not reacting". For each pie that maps to a filter dimension, run a dedicated pass that zeros out non-picked categories and recomputes the headline total:

```ts
function filterOrgStatusView(data: AdoptionMetrics, filters: DashboardFilters): AdoptionMetrics {
  const picks = filters.statuses.filter(s => ORG_STATUS_CATEGORIES.includes(s));
  if (picks.length === 0 || picks.length === ORG_STATUS_CATEGORIES.length) return data;
  const includes = (cat: string) => picks.includes(cat.toLowerCase());
  const nextDistribution = data.organizationsOverview.statusDistribution.map(slice => ({
    ...slice,
    value: includes(slice.category) ? slice.value : 0,
  }));
  const nextTotal = nextDistribution.reduce((sum, s) => sum + s.value, 0);
  return { ...data, organizationsOverview: {
    ...data.organizationsOverview,
    total: nextTotal.toLocaleString("en-US"),
    active: includes("active") ? data.organizationsOverview.active : "0",
    /* …per-slice KPIs… */
    statusDistribution: nextDistribution,
  }};
}
```

Chain the per-dimension passes after the scalar: `filterProviderView(filterOrgStatusView(scaled, filters), filters)`. Donuts and per-category KPIs collapse to the selected cohort; everything else scales naturally.

**Rule of thumb:** if a card shows **ratios** (donut, stacked %), it needs a per-dimension pass. If it shows **totals** (KPI, line, stacked column of absolute values), the scalar is enough.

### Outbound links carry filter state

Dashboard links to other views (Organizations / Entitlements / entity detail) should hydrate the destination with the same filter cohort. Add a `with<Feature>Filters(path, filters)` helper to the filter-context file:

```ts
// features/<feature>/components/<Feature>FiltersContext.ts
export function withDashboardFilters(path: string, filters: DashboardFilters): string {
  const params = new URLSearchParams();
  if (filters.statuses.length > 0) params.set("statuses", filters.statuses.join(","));
  if (filters.providers.length > 0) params.set("providers", filters.providers.join(","));
  params.set("from", filters.from.toISOString().slice(0, 10));
  params.set("to", filters.to.toISOString().slice(0, 10));
  const query = params.toString();
  if (!query) return path;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}${query}`;
}
```

Tabs read it via a one-liner local helper so link call-sites stay short, and per-link params (`?status=active`) coexist with the appended filter state:

```tsx
const { filters } = useDashboardFilters();
const link = (path: string) => withDashboardFilters(path, filters);
…
<KpiTile linkTo={link(`${ORGANIZATION_PATHS.root}?status=active`)} />
```

Destinations don't have to consume the params immediately — the state travels through so wiring the receiving view is a one-liner later.

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
7. **Styles** — if a shared presentation layer exists (project bindings skill lists the prefix + class vocabulary), reuse those classes; otherwise use CSS Modules (`<Component>.module.scss` sibling) for per-feature styles. Add modifiers via `&--variant` rather than one-off CSS.
8. **Verify** — `cd frontend && npm run typecheck` **and** `npm run build` (SCSS errors only show at build); run `npx prettier --write` on touched files.

## Iteration rhythm for POC work

POC sessions are visual-iteration heavy. The user rolls back layout decisions ~1 in 3 times. To keep churn low:

- **Propose + ask on design-trade-off decisions.** Panel order, column spans, chart heights, chip variants, filter placement, hover styles — present one option with a one-line rationale and wait, don't commit silently.
- **Keep each change tightly scoped.** One concern per iteration (grid ratios, OR KPI typography, OR hover effect) — mixing them makes rollback expensive.
- **Trust the roll-back.** If asked to revert, do it cleanly (not partially) and remove orphaned i18n keys / SCSS blocks / imports in the same step.

## POC anti-patterns

(General ones — root DS imports, Fast-Refresh split, guessing icon/SCSS names, premature extraction — live in `mpt-frontend-standards`.)

- Importing JSON directly in a tab/component — breaks the swap-to-real-API story.
- Inline response shapes in a tab/component — belongs in `api/model.ts`.
- Rebuilding chart series arrays inside the component body — triggers amCharts root rebuild on every render; keep them at module scope.
- Custom chrome that mimics DS primitives — if it looks like a `Navigation.CollapseButton` it must be one, otherwise ask.
- Using `Dropdown` for multi-value — closes on each selection; use the `Popover` + `Checkbox` multi-select recipe instead.
- `grid-template-rows: 0fr → 1fr` for height animation — intrinsic-sized form controls leak out of the clipped row in some browsers; use `max-height` + `overflow:hidden` + `visibility` instead.
- Re-adding an import to a file whose target was previously deleted — check with the Grep tool before trusting a paste.
- **Uniform scalar scaling without per-category filtering for distribution donuts** — scaling every slice by the same factor preserves the pie's ratios, so the user reports "the donut's not reacting" even though the headline KPI moved. Always pair the scalar with a per-dimension `filterXView` pass (see **Mock-side reactivity patterns**).
- **Draft + Apply for simple selects** — single-value changes don't need an Apply button; a sticky Apply on every input is friction. Reserve draft/apply for compound inputs (date range) where a partial pick would commit a broken filter.
- **Omitting `placeholderData: keepPreviousData`** on `useQuery` under a filter sidebar — every filter change makes `if (!data) return null` unmount the panel grid and amCharts restarts its load animation. Users read it as a full-page reload. Always keep previous data visible during refetch, pair with an overlay for the "refreshing" affordance.
- **Dropping arbitrary content into a SWO `Popover` without a surface** — `.popover__content` only sets position/z-index; no background, no border, no shadow. Content inside must bring its own `background`, `border`, `border-radius`, `box-shadow` or the popover appears unstyled against the page.
- **Trying to use `Navigation.SideNav` for arbitrary left-column content** — it accepts `groups: SideNavItem[]` only (navigation primitive). Compose your own `<aside>` matching its visual spec (250px / 72px / `border-right` only) rather than trying to coerce form content through it.
- **Reusing the same colour palette for two orthogonal dimensions on the same screen** (e.g. green/orange/gray for both status *and* providers) — users read the colour as the meaning, so collisions across adjacent cards confuse the eye. Give each dimension its own hue family.
