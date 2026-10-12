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
