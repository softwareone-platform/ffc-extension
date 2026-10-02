# Design system components — usage recipes

How we actually assemble `@swo/design-system/*` components (and the shared
`~shared/components/*` wrappers around them). Companion to
[`design-system.md`](./design-system.md), which covers the meta rules
(subpath imports, verified gaps, icon names, SCSS tokens, chart palettes).

Scope split:

- **This doc** — "I need to render a Grid / Modal / Chart / Panel. Where do
  the pieces come from and how do they fit?"
- **[`design-system.md`](./design-system.md)** — "How do I import, what are
  the known gaps, which SCSS tokens exist?"
- **[`modals.md`](./modals.md)** — the app-level modal pattern
  (`useModalToggle`, `use<Entity>FormController`). References the DS Modal
  piece documented here.

## Panel + KpiTile

Both come from `~shared/components/panel`, which wraps the DS primitives with
the project's defaults.

```tsx
import { Panel, KpiTile } from "~shared/components/panel";

<Panel title={t("overview:title")}>
  <div className={"ffc-kpi-row"}>  {/* --four / --quad / --column for other layouts */}
    <KpiTile label={t("overview:total")} value={data.total} />
    <KpiTile label={t("overview:active")} value={data.active} trend={"up"} />
  </div>
</Panel>
```

**`Panel` chrome gotcha** — `Panel` wraps `Card`, which already ships
padding / radius / background. Don't restate chrome in `.ffc-panel` or
you'll double-pad.

**`KpiTile` linkable variant** — pass `linkTo` to wrap the Card in a
`react-router-dom` `<Link>` with a chevron affordance and hover animation:

```tsx
import { PATHS as ORGANIZATION_PATHS } from "~features/organizations/paths";

<KpiTile
  label={t("overview:active")}
  value={data.active}
  trend={"up"}
  linkTo={`${ORGANIZATION_PATHS.root}?status=active`}
/>
```

The target feature still needs to parse the query param to actually
pre-filter — `linkTo` wires nav + affordance only.

## Grid

Two flavours:

- **`useGridInMemory`** — client-side sort/filter against an in-memory row
  array. Use for small datasets already in hand (mock JSON, computed
  aggregates, cached slices).
- **`useGridAsync`** / **`useReactQueryRqlGrid`** — server-side via RQL,
  used by the entity grids in `features/*/list/`. See
  [`api-hooks.md`](./api-hooks.md) for the hook shapes behind them.

### In-memory grid with initial sort

```tsx
import {
  Grid,
  GridCellSimple,
  GridColumnDefinition,
  GridFieldDefinition,
  GridFieldSortOperation,
  useGridInMemory,
} from "@swo/design-system/grid";

const INITIAL_SORT: GridFieldSortOperation[] = [
  { field: "creationDate", direction: "desc" },
];

const columns = useMemo((): GridColumnDefinition<Row>[] => [
  {
    name: "creationDate",
    title: t("creationDate"),
    cell: (item) => <GridCellSimple>{formatDate(item.creationDate)}</GridCellSimple>,
  },
  /* ... */
], [t, formatDate]);

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

### `GridFilterFieldType` values

Supported types (grep
[`@swo/design-system/grid/src/lib/model.d.ts`](../../frontend/node_modules/@swo/design-system/grid/src/lib/model.d.ts)):

```
'text' | 'number' | 'date' | 'datetime' | 'boolean' | 'list'
```

**`list` gotcha**: requires `options: {value, label}[]` and the stored row
value is compared as a **string**. Don't use `list` for numeric columns
(e.g. a maturity-level 0-4) unless you're willing to store the value as a
string too; use `number` instead.

### Date columns

Store ISO (`YYYY-MM-DD`) in the row data; format in the cell with
`useFormatDate` from `~shared/hooks/useFormatDate`. That keeps the stored
value sortable and lets the display formatter respect the user's locale.

### Status / threshold chips in cells

Chips (`@swo/design-system/chip`) with
`color="success"|"warning"|"gray"|"primary"` for status / threshold
indicators. Default `type` is filled; use `type="outline"` only when the
Storybook default doesn't fit.

```tsx
<Chip label={tStatus(item.status)} color={item.status === "paid" ? "success" : "primary"} />
```

### Grid testing

Grid wrappers have their own spec recipe in
[`testing.md`](./testing.md) and
[`.claude/skills/mpt-module-testing/SKILL.md`](../../.claude/skills/mpt-module-testing/SKILL.md)
(mock `@swo/design-system/grid` at the full subpath, use shared mocks from
`~test-utils/mocks/designSystemGrid`, capture `onAction` via the config
hook spy).

## Modal

Two layers:

- **`@swo/design-system/modal`** provides the raw modal shell: open/close,
  header, body, wizard integration. **Don't call it directly** — go through
  the app wrapper.
- **`~shared/components/modal/Modal`** wraps the DS modal with the project's
  common defaults (width, cancel/submit action buttons via
  `ModalCancelButton`). This is what features render.

Full application pattern — `useModalToggle`, `ModalCloseResult` close
contract, `use<Entity>FormController` plumbing, wizard vs simple-form
layouts, file structure per feature — lives in
[`modals.md`](./modals.md). Don't reach for `@swo/design-system/modal`
directly in feature code; follow that doc.

**Testing modals** — mock the shared `Modal.tsx` wrapper with a callback
capture spy (`~test-utils/mocks/modal`), not the raw DS modal. Full recipe
in [`.claude/skills/mpt-module-testing/SKILL.md`](../../.claude/skills/mpt-module-testing/SKILL.md).

## Charts

Shared primitives from `~shared/components/charts` wrap amCharts:

- **`XyChart`** — line / area / column; props `stacked`, `horizontal`.
- **`DonutChart`** — pass explicit `height={240+}` in wide panels (DS
  default of `150` looks tiny — see
  [`design-system.md`](./design-system.md) gap table).
- **`ChartLegend`** — manual legend; takes `items={ name, color }[]` with
  optional `layout={"horizontal"}`.

### Series + colour arrays live at module scope

amCharts rebuilds its root whenever `series` / `colors` identity changes.
Build them inside the component body and the chart tears down + rebuilds on
every render.

```tsx
// Module scope: stable across renders.
const SPEND_SERIES: XySeriesDef[] = [
  { field: "spend", name: "Spend", color: CHART_COLORS.blue, kind: "line" },
];

function SpendPanel({ data }: Props) {
  return <XyChart data={data} categoryField={"month"} series={SPEND_SERIES} />;
}
```

### Palette

`CHART_COLORS` and `PROVIDER_COLORS` from `~shared/components/charts` are
the canonical palettes. See
[`design-system.md`](./design-system.md#chart-palettes) for the full rule.

## Multi-select (compose `Popover` + `Checkbox`)

No DS component fits (see the gap in
[`design-system.md`](./design-system.md#verified-ds-gaps-and-the-workarounds)).
Build from DS primitives with a labelable `<button>` trigger:

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
  const toggle = (v: T) =>
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  const summary =
    value.length === 0
      ? placeholder
      : options.filter((o) => value.includes(o.value)).map((o) => o.label).join(", ");

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
            {options.map((o) => (
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

**Why not `Dropdown`**: it fires `isOpenChange(false)` on every
`onItemSelected`, closing the list after each tick — poor multi-select UX.

**Why plain `<button>`**: DS `Button` has strict props with no `id` or ARIA
passthrough. For a labelable combobox trigger a native `<button>` with
`aria-labelledby` is cleaner.

## Navigation

Shell shape:

```tsx
<Navigation>
  <Navigation.SideNav level={1} groups={sideNavGroups} />
  <Navigation.Content>
    <Navigation.TopBar items={topBarItems} />
    <Outlet />
  </Navigation.Content>
</Navigation>
```

**Collapsed-by-default** — no prop. Mount a tiny helper that
`requestAnimationFrame`s then clicks
`[data-testid="navigation__collapse-button"]`.

**`Navigation.SideNav.groups.items`** are strictly link lists; `children`
are silently dropped. Use for navigation only — form content goes in a
sibling panel or a popover triggered from a nav item.

## Chip

```tsx
import { Chip } from "@swo/design-system/chip";

<Chip label={tStatus(item.status)} color={"success"} />        // filled, green
<Chip label={"Draft"} color={"gray"} type={"outline"} />         // outlined, muted
```

Colour vocabulary: `success | warning | gray | primary` (+ others in the
Storybook). `type={"outline"}` only when the filled default collides with
the surrounding chrome.

## Date picker

```tsx
import { DatePicker } from "@swo/design-system/date-picker";

<DatePicker<Date>
  label={t("from")}
  value={range.from}
  maxDate={range.to}
  onChange={(from) => setRange((current) => ({ ...current, from }))}
/>
```

Pass `minDate` / `maxDate` to bound an interval; the picker won't let the
user cross the bound.

## See also

- [Design system (meta)](./design-system.md) — subpath imports, verified
  gaps, icon names, SCSS tokens, `.ffc-*` layout classes, chart palettes.
- [Modal pattern](./modals.md) — `useModalToggle`, `use<Entity>FormController`,
  simple-form vs wizard layouts.
- [API hook conventions](./api-hooks.md) — the hook shapes behind
  `useGridAsync` / `useReactQueryRqlGrid`.
- [Testing conventions](./testing.md) — how DS components are mocked in
  specs.
- [`.claude/skills/mpt-design-system/SKILL.md`](../../.claude/skills/mpt-design-system/SKILL.md)
  — Claude Code skill with multi-step composition recipes and composition
  gotchas layered on top of this doc. **This doc wins on drift.**
