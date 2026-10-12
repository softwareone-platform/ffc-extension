# Design system & presentation conventions

How we consume `@swo/design-system`, `@swo/design-tokens`, and the shared
`.ffc-*` style primitives. "Don't invent what already exists" is the thread:
the wrong icon name silently renders nothing, an invented SCSS token fails
only at `npm run build` (`tsc` doesn't process SCSS, so it won't catch it),
and the wrong import path silently breaks jest mocks or inflates the bundle.

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
raw hex literals (not CSS vars) — amCharts reads config at mount time, before
CSS variables resolve, so a token reference would evaluate to an empty
string. Centralise the hex values in a palette module when more than one
chart depends on them.

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

## SCSS tokens

The project does **not** currently ship a shared alias layer on top of
`@swo/design-tokens` — there is no `~shared/styles/_tokens.scss`. Feature
SCSS files consume the vendor's CSS custom properties **directly**:

```scss
.properties-section {
  display: grid;
  gap: var(--spacing-2);
  margin: 0 var(--spacing-1);
}
```

Available variable families (grep
[`node_modules/@swo/design-tokens/src/lib/`](../../frontend/node_modules/@swo/design-tokens/src/lib/)
for the full list):

- Spacing: `var(--spacing-0.5)` … `var(--spacing-4)` (and `--spacing-N`)
- Radius: `var(--radius-s)`, `var(--radius-m)`, `var(--radius-l)`
- Shadow: `var(--box-shadow-1)` … `var(--box-shadow-3)`
- Colour: `var(--brand-*)`, `var(--alerts-*-N)`, `var(--brand-type)` (text)
- Z-index: `var(--z-bottom)`, `var(--z-below)`, `var(--z-0)`, `var(--z-above)`, `var(--z-above-2)`, `var(--z-top)`
- Transition: `var(--transition)`

If you need SCSS variable form instead of CSS variables, import the vendor
module and use `$var-*` names (e.g. `$var-radius-m`, `$var-brand-primary`):

```scss
@use "@swo/design-tokens/src/lib/design-tokens-variables" as *;

.card { border-radius: $var-radius-m; }
```

**Do not invent** names like `$primary`, `$danger`, `$surface`, `$space-xs`
— they don't exist. An invented token fails only at `npm run build`
(`tsc` doesn't process SCSS, so it won't catch it).

Run `npm run build` after any SCSS change.

> **When a shared alias layer lands** (`~shared/styles/_tokens.scss`),
> replace this section with the alias table and link to the file.

## Component styling

The project does **not** currently ship a shared `.ffc-*` presentation
layer at `~shared/styles/_components.scss`. Features style themselves two
ways:

- **CSS Modules** (`<Component>.module.scss` imported as `styles.foo`) —
  default for component-local styling. Class names are hashed, so there's
  no cross-feature collision risk. See
  [`frontend/src/shared/components/CardSection.module.scss`](../../frontend/src/shared/components/CardSection.module.scss)
  and the `.module.scss` siblings alongside details-page components for
  canonical examples.
- **Plain `.scss` with CSS Modules disabled** (`<Component>.scss` imported
  for side effect, as in `~entries/StandaloneRoot.scss` or the modal
  flows) — only when global selectors are intentional.

**When a shared layout layer lands** (`~shared/styles/_components.scss`
under a shared `.ffc-*` namespace), the recommended pattern is `.ffc-<area>`
primitives (`tab-stack`, `panel-grid`, `kpi-row`, `chart-split`,
`filter-bar`, `multiselect`) with `&--variant` modifiers rather than one-off
CSS. A new primitive earns a class only after its shape repeats in a second
feature — see the extraction threshold in
[`.claude/skills/mpt-frontend-standards/SKILL.md`](../../.claude/skills/mpt-frontend-standards/SKILL.md#extraction-threshold).

## Chart palettes

Colour constants used across more than one chart should live in a single
project palette module (planned location in this project:
`~shared/components/charts`). Use the same constants in chart series
definitions and anywhere a legend / donut aside needs to match. **Keep chart
series arrays at module scope** — amCharts rebuilds its root whenever
`series` / `colors` identity changes.

```ts
// Module scope: stable across renders. Use raw hex until a palette module ships.
const SPEND_SERIES = [
  { field: "spend", name: "Spend", color: "#2d7af0", kind: "line" as const },
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
