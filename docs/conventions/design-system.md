# Design system & presentation conventions

How we consume `@swo/design-system`, `@swo/design-tokens`, and the shared
`.ffc-*` style primitives. "Don't invent what already exists" is the thread:
the wrong icon name silently renders nothing, the wrong SCSS token fails the
build silently from `tsc`, and the wrong import path silently breaks jest
mocks or inflates the bundle.

## Component sourcing: Storybook first

The design-system Storybook (https://storybook.platform.softwareone.com) is
the source of truth. Before building a new widget:

1. **Search Storybook.** Component names mirror the exports —
   `widgets-grid--in-memory-example` ↔ `@swo/design-system/grid`
   `useGridInMemory`.
2. **Partial match → ask, don't invent.** If the DS component covers only
   part of the behaviour, stop and discuss (custom wrapper, different DS
   recipe, or open a design-system request). Silently mimicking DS chrome in
   `.ffc-*` CSS creates drift.
3. **External only when nothing fits.** Pick an existing dep (amCharts for
   charts, `react-hook-form` for forms) and briefly justify.

## Import discipline: always subpath

Always import by subpath, **never** from the `@swo/design-system` root:

```ts
// ✅
import { Button } from "@swo/design-system/button";
import { Grid } from "@swo/design-system/grid";

// ❌
import { Button, Grid } from "@swo/design-system";
```

Two reasons that compound:

1. **Bundle size.** Subpath imports pull one component's dependency graph;
   the root barrel pulls everything (100s of KB extra per import). The tabs
   bundle alone is 769 KB — most of that from accidental root imports.
2. **Jest mock resolution.** `jest.mock("@swo/design-system/grid", …)` only
   matches the exact path the source imports. A root-barrel source + subpath
   mock (or vice-versa) silently no-ops and the real module runs.

**Design tokens** (`@swo/design-tokens`): SCSS only. In amCharts configs use
raw hex via `CHART_COLORS` (CSS vars haven't resolved yet when amCharts reads
them).

## Verified DS gaps (and the workarounds)

| Need | Status | What to do |
|---|---|---|
| Multiselect field | ❌ Nothing fits. `Select` is single value; `Dropdown` closes on every `onItemSelected`; `SelectableFilter` is modal-heavy and needs an async `apiCall`. | Build from `Popover` + `Checkbox` list (recipe in `mpt-poc-builder` skill). |
| Button with `id` / ARIA | ❌ Strict `ButtonProps` has no `id` or ARIA passthrough. | For a labelable combobox trigger use a plain `<button>` with `aria-labelledby` + a visible `<span id>` label. |
| `Icon.name` | ⚠️ Strict string-literal union. `arrow_drop_down`, `arrow_down`, etc. don't exist. | Use `expand_more` for dropdowns, `arrow_forward_ios` / `arrow_back_ios` for chevrons, `info`, `filter_alt`. Grep [`node_modules/@swo/design-system/icon/src/lib/icon-paths/`](../../frontend/node_modules/@swo/design-system/icon/src/lib/icon-paths/) before guessing. |
| `DonutChart` default size | ⚠️ `height={150}` — tiny in wide panels. | Pass explicit `height={240+}` in large panels. |
| `Navigation.SideNav.groups.items` | ⚠️ Strictly link lists; `children` are silently dropped. | Navigation only. Form content goes in a sibling panel or a popover triggered from a nav item. |
| `Navigation` default-collapsed | ❌ No prop. | Mount a tiny helper that `requestAnimationFrame`s then clicks `[data-testid="navigation__collapse-button"]`. |
| `Panel` chrome | ⚠️ `Panel` wraps `Card` which already ships padding / radius / background. | Don't restate chrome in `.ffc-panel` or you'll double-pad. |

When you discover a new gap, add it here with the same shape: _what you needed_
→ _status_ → _workaround_. Future readers skip the discovery pain.

## Icon names: do not guess

`Icon.name` is a strict string-literal union — the TypeScript error is clear,
but easy to burn 10 minutes guessing synonyms. Keep a short mental cache:

| Intent | Icon |
|---|---|
| Dropdown / disclosure down | `expand_more` |
| Chevron right / forward | `arrow_forward_ios` |
| Chevron left / back | `arrow_back_ios` |
| Information callout | `info` |
| Filter trigger | `filter_alt` |

For anything else, grep
[`frontend/node_modules/@swo/design-system/icon/src/lib/icon-paths/`](../../frontend/node_modules/@swo/design-system/icon/src/lib/icon-paths/).

## SCSS token vocabulary

[`frontend/src/shared/styles/_tokens.scss`](../../frontend/src/shared/styles/_tokens.scss)
defines a fixed set of aliases on top of `@swo/design-tokens`. **Do not
invent** names like `$primary`, `$danger`, `$warning` — they don't exist and
the SCSS build silently fails (TypeScript doesn't catch it; only
`npm run build` does).

| Alias                           | Use for                                              |
| ------------------------------- | ---------------------------------------------------- |
| `$surface`, `$surface-muted`    | Backgrounds (white, muted gray)                      |
| `$border-subtle`                | 1 px borders                                         |
| `$text-muted`, `$text-strong`   | Secondary / primary text colour                      |
| `$positive`, `$negative`        | Up / down / success / danger text colour             |
| `$space-xs` … `$space-xl`       | `--spacing-0.5` through `--spacing-4`                |
| `$radius-card`                  | Card / panel rounding (8 px)                         |
| `$panel-grid-breakpoint`        | Breakpoint where 2-col grid collapses to 1          |

Run `npm run build` after any SCSS change — `npx tsc --noEmit` won't catch
token errors.

## Shared `.ffc-*` class primitives

Feature-grid primitives live in
[`frontend/src/shared/styles/_components.scss`](../../frontend/src/shared/styles/_components.scss)
under the `.ffc-*` namespace. Use existing classes before adding new ones:

- Layout: `.ffc-tab-stack`, `.ffc-panel-grid`, `.ffc-panel`,
  `.ffc-panel--full`, `.ffc-panel--span-4`, `.ffc-panel--span-8`
- KPI rows: `.ffc-kpi-row`, `.ffc-kpi-row--four`, `.ffc-kpi-row--quad`,
  `.ffc-kpi-row--column`
- Chart composition: `.ffc-chart-split`, `.ffc-chart-split--triple`, `.ffc-legend`
- Filter affordances: `.ffc-filter-bar`, `.ffc-multiselect`

**Add modifiers** (`&--variant`) rather than one-off component CSS. A new
primitive earns a new class only after the shape repeats in a second feature.

## Chart palettes

`CHART_COLORS` and `PROVIDER_COLORS` from `~shared/components/charts` are the
canonical palettes. Use them in chart series definitions and anywhere a chart
colour needs to match a legend / donut aside. **Keep chart series arrays at
module scope** — amCharts rebuilds its root whenever `series` / `colors`
identity changes.

```ts
// Module scope: stable across renders.
const SPEND_SERIES: XySeriesDef[] = [
  { field: "spend", name: "Spend", color: CHART_COLORS.blue, kind: "line" },
];
```

## See also

- [Naming conventions](./naming.md) — file / folder casing (`PascalCase.tsx`,
  `kebab-case` folders, `.config.tsx` companions).
- [API hook conventions](./api-hooks.md) — the shape of the hooks components
  wire into DS primitives.
- [i18n conventions](./i18n.md) — labels passed into DS components come from
  `useFixedT`, never hard-coded strings.
- [`.claude/skills/mpt-poc-builder/SKILL.md`](../../.claude/skills/mpt-poc-builder/SKILL.md)
  — Claude Code skill with multi-step recipes built on top of these primitives
  (12-column panel grid, KPI tile, multi-select, chart composition, in-memory
  grid). **This doc wins on drift.**
- [`.claude/skills/mpt-frontend-standards/SKILL.md`](../../.claude/skills/mpt-frontend-standards/SKILL.md)
  — baseline conventions skill that defers to this doc for DS imports, icons,
  and SCSS tokens.
